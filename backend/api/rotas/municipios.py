"""Municípios da RMS: contorno no mapa, indicadores do IBGE e ficha resumo."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import Connection

from api.db import ano_mais_recente, conexao, linha, linhas
from api.dominios import Detalhe
from api.filtros import PADRAO_MUNICIPIO
from api.geojson import RESPOSTA_GEOJSON, colecao
from api.modelos import FichaMunicipio, IndicadoresMunicipio


router = APIRouter(prefix="/municipios", tags=["Municípios"])

# Tolerância da simplificação do contorno, em graus (~50 m).
# Deixa o GeoJSON ~6x menor sem diferença visível na escala da região.
TOLERANCIA_SIMPLES = 0.0005


@router.get("", responses=RESPOSTA_GEOJSON, summary="Contorno dos 27 municípios")
def listar_municipios(
    detalhe: Detalhe = Query(
        Detalhe.simples,
        description="'simples' (leve, para o mapa) ou 'completo' (contorno original do IBGE).",
    ),
    con: Connection = Depends(conexao),
):
    """GeoJSON com o contorno de cada município, a área e a população de 2022."""

    geometria = (
        "geometria"
        if detalhe == Detalhe.completo
        else f"ST_SimplifyPreserveTopology(geometria, {TOLERANCIA_SIMPLES})"
    )
    resultado = linhas(
        con,
        f"""
        SELECT cd_mun, nm_mun, area_km2, populacao_2022,
               ST_AsGeoJSON({geometria}, 6)::json AS geometria
        FROM vw_municipios_mapa
        ORDER BY nm_mun
        """,
    )
    return colecao(resultado, coluna_id="cd_mun")


@router.get(
    "/indicadores",
    response_model=list[IndicadoresMunicipio],
    summary="Indicadores de todos os municípios",
)
def listar_indicadores(con: Connection = Depends(conexao)):
    """Uma linha por município, com os números do IBGE (bom para tabelas e mapas coloridos)."""

    return linhas(con, "SELECT * FROM vw_indicadores_municipio ORDER BY nm_mun")


@router.get("/{cd_mun}", response_model=FichaMunicipio, summary="Ficha de um município")
def ficha_municipio(
    cd_mun: str = Path(pattern=PADRAO_MUNICIPIO, description="Código IBGE (7 dígitos)."),
    con: Connection = Depends(conexao),
):
    """Indicadores do IBGE + resumo da educação (escolas, cursos técnicos e superiores)."""

    indicadores = linha(
        con, "SELECT * FROM vw_indicadores_municipio WHERE cd_mun = :cd", {"cd": cd_mun}
    )
    if indicadores is None:
        raise HTTPException(404, "Município não encontrado na Região Metropolitana de Sorocaba.")

    ano_escolar = ano_mais_recente(con, "inep_escola")
    ano_superior = ano_mais_recente(con, "mec_cursos")

    educacao = linha(
        con,
        """
        WITH escolas AS (
            SELECT e.*,
                   EXISTS (
                       SELECT 1 FROM inep_curso_tecnico c
                       WHERE c.nu_ano_censo = e.nu_ano_censo
                         AND c.co_entidade = e.co_entidade
                         AND c.id_area_curso_profissional <> 999
                   ) AS tem_curso_tecnico
            FROM inep_escola e
            WHERE e.co_municipio = :cd AND e.nu_ano_censo = :ano_escolar
              AND e.tp_situacao_funcionamento = 1
        )
        SELECT
            (SELECT COUNT(*) FROM escolas) AS escolas_ativas,
            (SELECT COUNT(*) FROM escolas WHERE in_comum_medio_medio)
                AS escolas_ativas_ensino_medio,
            (SELECT COUNT(*) FROM escolas
              WHERE tem_curso_tecnico OR in_comum_medio_integrado OR in_itinerario_tecn_prof)
                AS escolas_ativas_educacao_profissional,
            (SELECT COUNT(*) FROM inep_curso_tecnico
              WHERE co_municipio = :cd AND nu_ano_censo = :ano_escolar
                AND id_area_curso_profissional <> 999) AS cursos_tecnicos,
            (SELECT COALESCE(SUM(qt_mat_curso_tec), 0) FROM inep_curso_tecnico
              WHERE co_municipio = :cd AND nu_ano_censo = :ano_escolar
                AND id_area_curso_profissional <> 999) AS matriculas_cursos_tecnicos,
            (SELECT COUNT(DISTINCT co_ies) FROM mec_cursos
              WHERE co_municipio = :cd AND nu_ano_censo = :ano_superior AND tp_dimensao = 1)
                AS instituicoes_presenciais,
            (SELECT COUNT(*) FROM mec_cursos
              WHERE co_municipio = :cd AND nu_ano_censo = :ano_superior AND tp_dimensao = 1)
                AS cursos_superiores_presenciais,
            (SELECT COUNT(*) FROM mec_cursos
              WHERE co_municipio = :cd AND nu_ano_censo = :ano_superior AND tp_dimensao = 2)
                AS cursos_superiores_ead
        """,
        {"cd": cd_mun, "ano_escolar": ano_escolar, "ano_superior": ano_superior},
    )

    return {
        "cd_mun": indicadores["cd_mun"],
        "nm_mun": indicadores["nm_mun"],
        "indicadores": indicadores,
        "educacao": {
            **educacao,
            "ano_censo_escolar": ano_escolar,
            "ano_censo_superior": ano_superior,
        },
    }
