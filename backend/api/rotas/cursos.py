"""Cursos técnicos (Censo Escolar) e cursos superiores (Censo da Educação Superior)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Connection

from api.db import ano_mais_recente, conexao, linhas
from api.dominios import ROTULOS, Grau, Modalidade, Rede
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
from api.modelos import CursoSuperior, CursoTecnico, InstituicaoNoMunicipio, Pagina


router = APIRouter(tags=["Cursos"])


@router.get(
    "/cursos-tecnicos",
    response_model=Pagina[CursoTecnico],
    summary="Cursos técnicos por escola",
)
def cursos_tecnicos(
    municipio: str | None = Query(None, pattern=PADRAO_MUNICIPIO, description=DESCRICAO_MUNICIPIO),
    area: int | None = Query(None, description="Código da área (veja /filtros). 999 = Normal/Magistério."),
    escola: int | None = Query(None, ge=1, description="Código INEP da escola."),
    incluir_magisterio: bool = Query(True, description="false = sem o curso Normal/Magistério."),
    busca: str | None = Query(
        None, min_length=2, max_length=100, description=DESCRICAO_BUSCA + " Procura no curso e na escola."
    ),
    ano: int | None = Query(None, ge=2000, le=2100, description=DESCRICAO_ANO),
    pag: Paginacao = Depends(paginacao),
    con: Connection = Depends(conexao),
):
    c = Condicoes()
    c.adicionar("nu_ano_censo = :ano", ano=ano or ano_mais_recente(con, "inep_escola"))
    if municipio:
        c.adicionar("co_municipio = :municipio", municipio=municipio)
    if area is not None:
        c.adicionar("id_area_curso_profissional = :area", area=area)
    if escola:
        c.adicionar("co_entidade = :escola", escola=escola)
    if not incluir_magisterio:
        c.adicionar("NOT e_normal_magisterio")
    c.busca(["no_curso_educ_profissional", "no_entidade"], busca)

    itens = linhas(
        con,
        f"""
        SELECT *, COUNT(*) OVER () AS _total
        FROM vw_cursos_tecnicos
        {c.where}
        ORDER BY no_curso_educ_profissional, no_entidade
        LIMIT :limite OFFSET :deslocamento
        """,
        {**c.params, **pag.params},
    )
    return pagina_de(itens, pag)


def condicoes_superior(
    con: Connection,
    ano: int | None,
    municipio: str | None,
    ies: int | None,
    modalidade: Modalidade | None,
    rede: Rede | None,
) -> Condicoes:
    c = Condicoes()
    c.adicionar("nu_ano_censo = :ano", ano=ano or ano_mais_recente(con, "mec_cursos"))
    if municipio:
        c.adicionar("co_municipio = :municipio", municipio=municipio)
    if ies:
        c.adicionar("co_ies = :ies", ies=ies)
    if modalidade:
        c.adicionar("e_presencial = :presencial", presencial=modalidade == Modalidade.presencial)
    if rede:
        c.adicionar("ds_rede = :rede", rede=ROTULOS[rede])
    return c


@router.get(
    "/cursos-superiores",
    response_model=Pagina[CursoSuperior],
    summary="Cursos de graduação por município de oferta",
)
def cursos_superiores(
    municipio: str | None = Query(None, pattern=PADRAO_MUNICIPIO, description=DESCRICAO_MUNICIPIO),
    ies: int | None = Query(None, ge=1, description="Código da instituição (co_ies)."),
    modalidade: Modalidade | None = Query(
        None, description="presencial = oferecido no município; ead = EAD com alunos no município."
    ),
    grau: Grau | None = Query(None, description="Grau acadêmico."),
    area: str | None = Query(
        None, max_length=200, description="Área geral CINE, exatamente como em /filtros."
    ),
    rede: Rede | None = Query(None, description="Rede pública ou privada."),
    gratuito: bool | None = Query(None, description="true = só cursos gratuitos."),
    apenas_com_matricula: bool = Query(False, description="true = só cursos com aluno matriculado."),
    busca: str | None = Query(
        None, min_length=2, max_length=100,
        description=DESCRICAO_BUSCA + " Procura no curso, no nome e na sigla da instituição.",
    ),
    ano: int | None = Query(None, ge=2000, le=2100, description=DESCRICAO_ANO),
    pag: Paginacao = Depends(paginacao),
    con: Connection = Depends(conexao),
):
    """Uma linha por curso em cada município.

    Um curso EAD aparece em todo município onde tem aluno, por isso
    use `modalidade=presencial` para ver só o que funciona na cidade.
    """

    c = condicoes_superior(con, ano, municipio, ies, modalidade, rede)
    if grau:
        c.adicionar("ds_grau_academico = :grau", grau=ROTULOS[grau])
    if area:
        c.adicionar("no_cine_area_geral = :area", area=area)
    if gratuito is not None:
        c.adicionar("COALESCE(e_gratuito, FALSE) = :gratuito", gratuito=gratuito)
    if apenas_com_matricula:
        c.adicionar("com_matricula")
    c.busca(["no_curso", "no_ies", "COALESCE(sg_ies, '')"], busca)

    itens = linhas(
        con,
        f"""
        SELECT *, COUNT(*) OVER () AS _total
        FROM vw_cursos_superiores
        {c.where}
        ORDER BY e_presencial DESC, no_curso, no_ies, no_municipio
        LIMIT :limite OFFSET :deslocamento
        """,
        {**c.params, **pag.params},
    )
    return pagina_de(itens, pag)


@router.get(
    "/instituicoes",
    response_model=Pagina[InstituicaoNoMunicipio],
    summary="Faculdades por município",
)
def instituicoes(
    municipio: str | None = Query(None, pattern=PADRAO_MUNICIPIO, description=DESCRICAO_MUNICIPIO),
    modalidade: Modalidade | None = Query(
        None, description="presencial = só instituições com curso presencial no município."
    ),
    rede: Rede | None = Query(None, description="Rede pública ou privada."),
    busca: str | None = Query(None, min_length=2, max_length=100, description=DESCRICAO_BUSCA),
    ano: int | None = Query(None, ge=2000, le=2100, description=DESCRICAO_ANO),
    pag: Paginacao = Depends(paginacao),
    con: Connection = Depends(conexao),
):
    """Uma linha por instituição em cada município, com a contagem de cursos.

    Ordenada pelas que têm mais cursos presenciais.
    """

    c = condicoes_superior(con, ano, municipio, None, modalidade, rede)
    c.busca(["no_ies", "COALESCE(sg_ies, '')"], busca)

    itens = linhas(
        con,
        f"""
        SELECT co_ies, no_ies, sg_ies, ds_rede, ds_organizacao_academica,
               co_municipio, no_municipio, sede_no_municipio,
               COUNT(*) FILTER (WHERE e_presencial) AS qt_cursos_presenciais,
               COUNT(*) FILTER (WHERE NOT e_presencial) AS qt_cursos_ead,
               COALESCE(SUM(qt_matriculas), 0) AS qt_matriculas,
               COUNT(*) OVER () AS _total
        FROM vw_cursos_superiores
        {c.where}
        GROUP BY co_ies, no_ies, sg_ies, ds_rede, ds_organizacao_academica,
                 co_municipio, no_municipio, sede_no_municipio
        ORDER BY qt_cursos_presenciais DESC, qt_matriculas DESC, no_ies
        LIMIT :limite OFFSET :deslocamento
        """,
        {**c.params, **pag.params},
    )
    return pagina_de(itens, pag)
