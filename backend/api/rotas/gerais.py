"""Opções para os filtros do site, origem dos dados e situação da API."""

from fastapi import APIRouter, Depends
from sqlalchemy import Connection, text

from api.db import ano_mais_recente, conexao, linhas
from api.dominios import Dependencia, Grau, Modalidade, Rede, opcoes
from api.modelos import Carga, OpcoesDeFiltro, Saude


router = APIRouter(tags=["Geral"])


@router.get("/filtros", response_model=OpcoesDeFiltro, summary="Opções para os filtros do site")
def opcoes_de_filtro(con: Connection = Depends(conexao)):
    """Listas prontas para montar os campos de seleção do frontend.

    O `valor` de cada opção é o que se manda nos outros endereços.
    """

    ano_escolar = ano_mais_recente(con, "inep_escola")
    ano_superior = ano_mais_recente(con, "mec_cursos")

    municipios = linhas(
        con, "SELECT cd_mun AS valor, nm_mun AS rotulo FROM ibge_municipios ORDER BY nm_mun"
    )
    areas_tecnicas = linhas(
        con,
        """
        SELECT DISTINCT id_area_curso_profissional::text AS valor,
               no_area_curso_profissional AS rotulo
        FROM inep_curso_tecnico
        WHERE nu_ano_censo = :ano AND id_area_curso_profissional IS NOT NULL
        ORDER BY rotulo
        """,
        {"ano": ano_escolar},
    )
    areas_cine = linhas(
        con,
        """
        SELECT DISTINCT no_cine_area_geral AS valor, no_cine_area_geral AS rotulo
        FROM mec_cursos
        WHERE nu_ano_censo = :ano AND no_cine_area_geral IS NOT NULL
        ORDER BY rotulo
        """,
        {"ano": ano_superior},
    )

    return {
        "municipios": municipios,
        "dependencias": opcoes(Dependencia),
        "areas_tecnicas": areas_tecnicas,
        "modalidades": opcoes(Modalidade),
        "graus_academicos": opcoes(Grau),
        "redes": opcoes(Rede),
        "areas_cine": areas_cine,
    }


@router.get("/fontes", response_model=list[Carga], summary="De onde vêm os dados")
def fontes(con: Connection = Depends(conexao)):
    """Última carga de cada arquivo oficial: órgão, fonte, data e quantidades.

    Serve para o rodapé "dados atualizados em..." e para a página de fontes.
    """

    return linhas(con, "SELECT * FROM vw_ultimas_cargas ORDER BY no_orgao, no_fonte, no_arquivo_origem")


@router.get("/saude", response_model=Saude, summary="A API está no ar?")
def saude(con: Connection = Depends(conexao)):
    con.execute(text("SELECT 1"))
    return {"status": "ok", "banco": "ok"}
