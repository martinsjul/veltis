"""Escolas do Censo Escolar: pontos no mapa, ficha e escolas sem coordenada."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import Connection

from api.db import ano_mais_recente, conexao, linha, linhas
from api.dominios import CODIGO_DEPENDENCIA, Dependencia
from api.filtros import (
    DESCRICAO_ANO,
    DESCRICAO_BUSCA,
    DESCRICAO_MUNICIPIO,
    PADRAO_MUNICIPIO,
    Condicoes,
    Paginacao,
    pagina_de,
    paginacao,
)
from api.geojson import RESPOSTA_GEOJSON, colecao
from api.modelos import EscolaDetalhe, EscolaSemLocalizacao, Pagina


router = APIRouter(prefix="/escolas", tags=["Escolas"])

EDUCACAO_PROFISSIONAL = (
    "(qt_cursos_tecnicos > 0 OR COALESCE(oferece_medio_integrado, FALSE) "
    "OR COALESCE(oferece_itinerario_tecnico, FALSE))"
)


def condicoes_escolas(
    con: Connection,
    ano: int | None,
    municipio: str | None,
    dependencia: list[Dependencia] | None,
    apenas_ativas: bool,
    ensino_medio: bool | None = None,
    educacao_profissional: bool | None = None,
    busca: str | None = None,
) -> Condicoes:
    """Filtros comuns aos endereços de escolas."""

    c = Condicoes()
    c.adicionar("nu_ano_censo = :ano", ano=ano or ano_mais_recente(con, "inep_escola"))

    if municipio:
        c.adicionar("co_municipio = :municipio", municipio=municipio)
    if dependencia:
        c.adicionar(
            "tp_dependencia = ANY(:dependencias)",
            dependencias=[CODIGO_DEPENDENCIA[d] for d in dependencia],
        )
    if apenas_ativas:
        c.adicionar("em_atividade")
    if ensino_medio is not None:
        c.adicionar(
            "COALESCE(oferece_ensino_medio, FALSE) = :ensino_medio", ensino_medio=ensino_medio
        )
    if educacao_profissional is not None:
        c.adicionar(f"{EDUCACAO_PROFISSIONAL} = :educ_prof", educ_prof=educacao_profissional)
    c.busca(["no_entidade"], busca)
    return c


@router.get("", responses=RESPOSTA_GEOJSON, summary="Escolas no mapa")
def mapa_escolas(
    municipio: str | None = Query(None, pattern=PADRAO_MUNICIPIO, description=DESCRICAO_MUNICIPIO),
    dependencia: list[Dependencia] | None = Query(
        None, description="Rede. Pode repetir: ?dependencia=estadual&dependencia=federal"
    ),
    apenas_ativas: bool = Query(True, description="Só escolas em atividade."),
    ensino_medio: bool | None = Query(None, description="true = só as que oferecem ensino médio."),
    educacao_profissional: bool | None = Query(
        None,
        description="true = só as com curso técnico, médio integrado ou itinerário técnico.",
    ),
    busca: str | None = Query(None, min_length=2, max_length=100, description=DESCRICAO_BUSCA),
    ano: int | None = Query(None, ge=2000, le=2100, description=DESCRICAO_ANO),
    con: Connection = Depends(conexao),
):
    """GeoJSON com um ponto por escola que tem coordenada.

    Em `metadados` vêm quantas escolas atendem aos filtros e quantas
    ficaram de fora do mapa por não terem coordenada.
    """

    c = condicoes_escolas(
        con, ano, municipio, dependencia, apenas_ativas, ensino_medio, educacao_profissional, busca
    )

    contagem = linha(
        con,
        f"""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE NOT tem_coordenada) AS sem_coordenada,
               COUNT(*) FILTER (WHERE ponto_confere_municipio = FALSE) AS ponto_fora_do_municipio
        FROM vw_escolas_mapa {c.where}
        """,
        c.params,
    )

    pontos = linhas(
        con,
        f"""
        SELECT co_entidade, no_entidade, co_municipio, no_municipio, ds_dependencia,
               em_atividade, oferece_ensino_medio,
               {EDUCACAO_PROFISSIONAL} AS educacao_profissional,
               qt_cursos_tecnicos, ponto_confere_municipio,
               ST_AsGeoJSON(geometria, 6)::json AS geometria
        FROM vw_escolas_mapa
        {c.where} AND tem_coordenada
        ORDER BY no_entidade
        """,
        c.params,
    )

    return colecao(
        pontos,
        coluna_id="co_entidade",
        metadados={
            "ano": c.params["ano"],
            "total_filtrado": contagem["total"],
            "no_mapa": len(pontos),
            "sem_coordenada": contagem["sem_coordenada"],
            "ponto_fora_do_municipio": contagem["ponto_fora_do_municipio"],
        },
    )


@router.get(
    "/sem-localizacao",
    response_model=Pagina[EscolaSemLocalizacao],
    summary="Escolas sem coordenada",
)
def escolas_sem_localizacao(
    municipio: str | None = Query(None, pattern=PADRAO_MUNICIPIO, description=DESCRICAO_MUNICIPIO),
    dependencia: list[Dependencia] | None = Query(None, description="Rede (pode repetir)."),
    apenas_ativas: bool = Query(True, description="Só escolas em atividade."),
    ano: int | None = Query(None, ge=2000, le=2100, description=DESCRICAO_ANO),
    pag: Paginacao = Depends(paginacao),
    con: Connection = Depends(conexao),
):
    """Escolas que não aparecem no mapa, para mostrar numa lista à parte."""

    c = condicoes_escolas(con, ano, municipio, dependencia, apenas_ativas)
    itens = linhas(
        con,
        f"""
        SELECT co_entidade, no_entidade, co_municipio, no_municipio, ds_dependencia,
               ds_situacao, ds_endereco, fonte_localizacao,
               COUNT(*) OVER () AS _total
        FROM vw_escolas_mapa
        {c.where} AND NOT tem_coordenada
        ORDER BY no_municipio, no_entidade
        LIMIT :limite OFFSET :deslocamento
        """,
        {**c.params, **pag.params},
    )
    return pagina_de(itens, pag)


@router.get("/{co_entidade}", response_model=EscolaDetalhe, summary="Ficha de uma escola")
def ficha_escola(
    co_entidade: int = Path(ge=1, description="Código INEP da escola."),
    ano: int | None = Query(None, ge=2000, le=2100, description=DESCRICAO_ANO),
    con: Connection = Depends(conexao),
):
    """Todos os dados da escola, com a lista dos cursos técnicos."""

    ano = ano or ano_mais_recente(con, "inep_escola")
    escola = linha(
        con,
        """
        SELECT nu_ano_censo, co_entidade, no_entidade, co_municipio, no_municipio,
               ds_dependencia, ds_localizacao, ds_situacao, em_atividade,
               oferece_ensino_medio, oferece_medio_integrado, oferece_normal_magisterio,
               oferece_itinerario_tecnico, qt_cursos_tecnicos, qt_matriculas_educ_profissional,
               ds_endereco, nu_cep, nu_telefone, fonte_localizacao, tp_metodo_localizacao,
               tem_coordenada, ponto_confere_municipio, latitude, longitude
        FROM vw_escolas_mapa
        WHERE co_entidade = :co AND nu_ano_censo = :ano
        """,
        {"co": co_entidade, "ano": ano},
    )
    if escola is None:
        raise HTTPException(404, "Escola não encontrada na Região Metropolitana de Sorocaba.")

    escola["cursos_tecnicos"] = linhas(
        con,
        """
        SELECT co_curso_educ_profissional, no_curso_educ_profissional,
               id_area_curso_profissional, no_area_curso_profissional,
               e_normal_magisterio, qt_mat_curso_tec
        FROM vw_cursos_tecnicos
        WHERE co_entidade = :co AND nu_ano_censo = :ano
        ORDER BY no_curso_educ_profissional
        """,
        {"co": co_entidade, "ano": ano},
    )
    return escola
