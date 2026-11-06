"""Lista única de escolas e faculdades para o mapa do site.

Cada item já vem com latitude e longitude, no formato que o frontend
usa (os mesmos campos do mockData do site).
"""

from enum import StrEnum

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Connection

from api.db import ano_mais_recente, conexao, linhas
from api.filtros import DESCRICAO_BUSCA, DESCRICAO_MUNICIPIO, PADRAO_MUNICIPIO, Condicoes
from api.modelos import InstituicaoNoMapa


router = APIRouter(prefix="/mapa", tags=["Mapa"])


class TipoNoMapa(StrEnum):
    escola = "escola"
    etec = "etec"
    fatec = "fatec"
    faculdade = "faculdade"


# ETECs aparecem no Censo Escolar como escolas estaduais com nome "ETEC ...".
E_ETEC = "(e.no_entidade ~* '^ETEC ' AND e.tp_dependencia = 2)"

SQL_ESCOLAS = """
SELECT
    'escola-' || e.co_entidade AS id,
    'INEP_ESCOLA' AS origem,
    CASE WHEN {e_etec} THEN 'ETEC' ELSE 'Escola' END AS tipo,
    e.no_entidade AS nome,
    NULL AS sigla,
    NULL AS "nomeInstituicao",
    e.co_entidade AS "codigoInep",
    NULL::int AS "codigoIes",
    e.no_municipio AS municipio,
    e.co_municipio AS "codigoMunicipio",
    'SP' AS uf,
    e.ds_dependencia AS rede,
    NULL AS "categoriaAdministrativa",
    e.ds_endereco AS endereco,
    NULL AS bairro,
    CASE WHEN length(e.nu_cep) = 8
         THEN substr(e.nu_cep, 1, 5) || '-' || substr(e.nu_cep, 6) END AS cep,
    e.nu_telefone AS telefone,
    ROUND(e.latitude::numeric, 6)::float AS latitude,
    ROUND(e.longitude::numeric, 6)::float AS longitude,
    e.ds_precisao_localizacao AS "precisaoLocalizacao",
    e.nu_ano_censo AS "anoCenso",
    e.ds_situacao AS "situacaoFuncionamento",
    e.oferece_ensino_medio AS "possuiEnsinoMedio",
    NULL AS "organizacaoAcademica",
    COALESCE((
        SELECT json_agg(json_build_object(
                   'codigo', c.co_curso_educ_profissional,
                   'nome', c.no_curso_educ_profissional,
                   'area', c.no_area_curso_profissional,
                   'matriculas', c.qt_mat_curso_tec)
               ORDER BY c.no_curso_educ_profissional)
        FROM inep_curso_tecnico c
        WHERE c.nu_ano_censo = e.nu_ano_censo AND c.co_entidade = e.co_entidade
    ), '[]'::json) AS cursos
FROM vw_escolas_mapa e
{where}
"""

SQL_FACULDADES = """
SELECT
    'ies-' || f.co_ies || '-' || f.id_local AS id,
    'MEC_IES' AS origem,
    CASE WHEN f.e_fatec THEN 'FATEC' ELSE 'Faculdade/Universidade' END AS tipo,
    f.no_local AS nome,
    f.sg_ies AS sigla,
    f.no_ies AS "nomeInstituicao",
    NULL::int AS "codigoInep",
    f.co_ies AS "codigoIes",
    f.no_municipio AS municipio,
    f.cd_mun AS "codigoMunicipio",
    'SP' AS uf,
    f.ds_rede AS rede,
    NULL AS "categoriaAdministrativa",
    f.ds_endereco AS endereco,
    f.no_bairro AS bairro,
    CASE WHEN length(f.nu_cep) = 8
         THEN substr(f.nu_cep, 1, 5) || '-' || substr(f.nu_cep, 6) END AS cep,
    NULL AS telefone,
    ROUND(f.latitude::numeric, 6)::float AS latitude,
    ROUND(f.longitude::numeric, 6)::float AS longitude,
    f.ds_precisao_localizacao AS "precisaoLocalizacao",
    f.nu_ano_censo AS "anoCenso",
    'Em atividade' AS "situacaoFuncionamento",
    FALSE AS "possuiEnsinoMedio",
    f.ds_organizacao_academica AS "organizacaoAcademica",
    f.js_cursos AS cursos
FROM vw_faculdades_mapa f
{where}
"""


@router.get(
    "/instituicoes",
    response_model=list[InstituicaoNoMapa],
    summary="Escolas e faculdades com latitude e longitude",
)
def instituicoes_no_mapa(
    municipio: str | None = Query(None, pattern=PADRAO_MUNICIPIO, description=DESCRICAO_MUNICIPIO),
    tipo: list[TipoNoMapa] | None = Query(
        None, description="Pode repetir: ?tipo=etec&tipo=fatec. Sem filtro = todos."
    ),
    busca: str | None = Query(None, min_length=2, max_length=100, description=DESCRICAO_BUSCA),
    apenas_ativas: bool = Query(True, description="Só escolas em atividade."),
    incluir_sem_coordenada: bool = Query(
        False,
        description="true = inclui escolas sem ponto (latitude e longitude vêm null).",
    ),
    con: Connection = Depends(conexao),
):
    """Uma lista só, pronta para desenhar os pinos no mapa.

    - **Escolas** (Censo Escolar): coordenada oficial do INEP/SEDUC.
    - **Faculdades**: um item por campus presencial na região, com a
      coordenada do levantamento em `backend/data/referencia`.
      `precisaoLocalizacao` diz se o ponto está no prédio, no número ou só na rua.
    - Escolas sem coordenada oficial podem ter ponto **geocodificado** a partir
      do endereço (IBGE CNEFE): `precisaoLocalizacao` = numero, numero_aproximado
      ou logradouro.
    """

    tipos = set(tipo or TipoNoMapa)
    resultado: list[dict] = []

    if tipos & {TipoNoMapa.escola, TipoNoMapa.etec}:
        c = Condicoes()
        c.adicionar("e.nu_ano_censo = :ano", ano=ano_mais_recente(con, "inep_escola"))
        if municipio:
            c.adicionar("e.co_municipio = :municipio", municipio=municipio)
        if apenas_ativas:
            c.adicionar("e.em_atividade")
        if not incluir_sem_coordenada:
            c.adicionar("e.tem_coordenada")
        if tipos.isdisjoint({TipoNoMapa.escola}):
            c.adicionar(E_ETEC)
        elif tipos.isdisjoint({TipoNoMapa.etec}):
            c.adicionar(f"NOT {E_ETEC}")
        c.busca(["e.no_entidade"], busca)

        resultado += linhas(con, SQL_ESCOLAS.format(e_etec=E_ETEC, where=c.where), c.params)

    if tipos & {TipoNoMapa.fatec, TipoNoMapa.faculdade}:
        c = Condicoes()
        if municipio:
            c.adicionar("f.cd_mun = :municipio", municipio=municipio)
        if tipos.isdisjoint({TipoNoMapa.faculdade}):
            c.adicionar("f.e_fatec")
        elif tipos.isdisjoint({TipoNoMapa.fatec}):
            c.adicionar("NOT f.e_fatec")
        c.busca(["f.no_local", "f.no_ies", "COALESCE(f.sg_ies, '')"], busca)
        resultado += linhas(con, SQL_FACULDADES.format(where=c.where), c.params)

    return sorted(resultado, key=lambda i: (i["municipio"] or "", i["nome"]))
