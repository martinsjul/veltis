import hashlib
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import requests
from geoalchemy2 import Geometry
from shapely.geometry import MultiPolygon
from sqlalchemy import text

from src.config.rms import CODIGOS_RMS
from src.database import engine


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "raw" / "ibge"
DATA_DIR.mkdir(parents=True, exist_ok=True)

URL_BASE_IBGE = (
    "https://geoftp.ibge.gov.br/"
    "organizacao_do_territorio/malhas_territoriais/"
    "malhas_municipais"
)


# ============================================================
# DESCOBRIR EDIÇÃO MAIS RECENTE
# ============================================================

def descobrir_ano_mais_recente() -> int:
    print("Consultando edições disponíveis no IBGE...")

    resposta = requests.get(
        f"{URL_BASE_IBGE}/",
        timeout=60,
    )

    resposta.raise_for_status()

    anos = re.findall(
        r"municipio_(\d{4})/",
        resposta.text,
    )

    if not anos:
        raise RuntimeError(
            "Nenhuma edição da Malha Municipal foi encontrada."
        )

    anos = [int(ano) for ano in anos]

    ano_mais_recente = max(anos)

    print(
        f"Edição mais recente encontrada: {ano_mais_recente}"
    )

    return ano_mais_recente


# ============================================================
# DOWNLOAD
# ============================================================

def baixar_malha(ano: int) -> tuple[Path, str]:
    nome_zip = f"SP_Municipios_{ano}.zip"

    url = (
        f"{URL_BASE_IBGE}/"
        f"municipio_{ano}/UFs/SP/"
        f"{nome_zip}"
    )

    caminho_final = DATA_DIR / nome_zip
    caminho_temporario = DATA_DIR / f"{nome_zip}.tmp"

    print(f"Baixando Malha Municipal {ano} de São Paulo...")

    resposta = requests.get(
        url,
        stream=True,
        timeout=180,
    )

    resposta.raise_for_status()

    with caminho_temporario.open("wb") as arquivo:
        for bloco in resposta.iter_content(
            chunk_size=1024 * 1024
        ):
            if bloco:
                arquivo.write(bloco)

    print("Download concluído.")

    return caminho_temporario, url


# ============================================================
# HASH SHA-256
# ============================================================

def calcular_hash(caminho: Path) -> str:
    sha256 = hashlib.sha256()

    with caminho.open("rb") as arquivo:
        for bloco in iter(
            lambda: arquivo.read(1024 * 1024),
            b"",
        ):
            sha256.update(bloco)

    return sha256.hexdigest()


# ============================================================
# FONTE DE DADOS
# ============================================================

def obter_id_fonte(conexao) -> int:
    resultado = conexao.execute(
        text(
            """
            SELECT id_fonte
            FROM fonte_dados
            WHERE no_orgao = 'IBGE'
              AND no_fonte = 'Malha Municipal'
            LIMIT 1
            """
        )
    ).scalar()

    if resultado is not None:
        return resultado

    resultado = conexao.execute(
        text(
            """
            INSERT INTO fonte_dados (
                no_orgao,
                no_fonte,
                ds_url_oficial,
                ds_periodicidade,
                ds_tipo_fonte,
                ds_observacao
            )
            VALUES (
                'IBGE',
                'Malha Municipal',
                :url,
                'Anual',
                'OFICIAL_PRINCIPAL',
                'Malha territorial oficial utilizada pelo Veltis.'
            )
            RETURNING id_fonte
            """
        ),
        {
            "url": f"{URL_BASE_IBGE}/"
        },
    )

    return resultado.scalar_one()


# ============================================================
# VERIFICAR SE A VERSÃO JÁ FOI PROCESSADA
# ============================================================

def hash_ja_processado(
    conexao,
    id_fonte: int,
    hash_arquivo: str,
) -> bool:

    resultado = conexao.execute(
        text(
            """
            SELECT 1
            FROM controle_ingestao
            WHERE id_fonte = :id_fonte
              AND ds_hash_sha256 = :hash
              AND ds_status = 'CONCLUIDA'
            LIMIT 1
            """
        ),
        {
            "id_fonte": id_fonte,
            "hash": hash_arquivo,
        },
    ).first()

    return resultado is not None


# ============================================================
# EXTRAÇÃO
# ============================================================

def extrair_malha(
    caminho_zip: Path,
    ano: int,
) -> Path:

    pasta_extraida = DATA_DIR / f"municipios_{ano}"

    if pasta_extraida.exists():
        shutil.rmtree(pasta_extraida)

    pasta_extraida.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Extraindo arquivo...")

    with zipfile.ZipFile(
        caminho_zip,
        "r",
    ) as arquivo_zip:

        arquivo_zip.extractall(pasta_extraida)

    shapefiles = list(
        pasta_extraida.rglob("*.shp")
    )

    if len(shapefiles) != 1:
        raise RuntimeError(
            "Era esperado exatamente 1 arquivo SHP, "
            f"mas foram encontrados {len(shapefiles)}."
        )

    return shapefiles[0]


# ============================================================
# PROCESSAMENTO E VALIDAÇÃO
# ============================================================

def processar_malha(
    caminho_shp: Path,
) -> tuple[gpd.GeoDataFrame, int]:

    print("Lendo arquivo com GeoPandas...")

    gdf = gpd.read_file(caminho_shp)

    quantidade_total = len(gdf)

    print(
        f"Municípios encontrados no arquivo de SP: "
        f"{quantidade_total}"
    )

    if "CD_MUN" not in gdf.columns:
        raise ValueError(
            "A coluna CD_MUN não existe no arquivo."
        )

    gdf["CD_MUN"] = (
        gdf["CD_MUN"]
        .astype(str)
        .str.strip()
    )

    gdf_rms = gdf[
        gdf["CD_MUN"].isin(CODIGOS_RMS)
    ].copy()

    # --------------------------------------------------------
    # Validação: quantidade
    # --------------------------------------------------------

    if len(gdf_rms) != 27:
        raise ValueError(
            "A RMS deve possuir exatamente 27 municípios. "
            f"Foram encontrados {len(gdf_rms)}."
        )

    # --------------------------------------------------------
    # Validação: códigos
    # --------------------------------------------------------

    encontrados = set(gdf_rms["CD_MUN"])

    faltantes = set(CODIGOS_RMS) - encontrados

    if faltantes:
        raise ValueError(
            "Municípios da RMS não encontrados: "
            f"{sorted(faltantes)}"
        )

    # --------------------------------------------------------
    # Validação: duplicidade
    # --------------------------------------------------------

    if gdf_rms["CD_MUN"].duplicated().any():
        raise ValueError(
            "Foram encontrados códigos de município duplicados."
        )

    # --------------------------------------------------------
    # Validação: CRS
    # --------------------------------------------------------

    if gdf_rms.crs is None:
        raise ValueError(
            "O arquivo não possui CRS definido."
        )

    if gdf_rms.crs.to_epsg() != 4674:
        print(
            f"Convertendo CRS {gdf_rms.crs} "
            "para EPSG:4674..."
        )

        gdf_rms = gdf_rms.to_crs(
            epsg=4674
        )

    # --------------------------------------------------------
    # Validação: geometria
    # --------------------------------------------------------

    if gdf_rms.geometry.isna().any():
        raise ValueError(
            "Existem municípios sem geometria."
        )

    if gdf_rms.geometry.is_empty.any():
        raise ValueError(
            "Existem geometrias vazias."
        )

    if not gdf_rms.geometry.is_valid.all():
        raise ValueError(
            "Existem geometrias inválidas."
        )

    # --------------------------------------------------------
    # Normalizar Polygon → MultiPolygon
    # --------------------------------------------------------

    gdf_rms["geometry"] = gdf_rms.geometry.apply(
        lambda geometria:
        MultiPolygon([geometria])
        if geometria.geom_type == "Polygon"
        else geometria
    )

    # --------------------------------------------------------
    # Campos previstos no dicionário
    # --------------------------------------------------------

    colunas = [
        "CD_MUN",
        "NM_MUN",
        "CD_RGI",
        "NM_RGI",
        "CD_RGINT",
        "NM_RGINT",
        "CD_UF",
        "NM_UF",
        "SIGLA_UF",
        "CD_REGIAO",
        "NM_REGIAO",
        "SIGLA_RG",
        "CD_CONCURB",
        "NM_CONCURB",
        "AREA_KM2",
        "geometry",
    ]

    colunas_faltantes = [
        coluna
        for coluna in colunas
        if coluna not in gdf_rms.columns
    ]

    if colunas_faltantes:
        raise ValueError(
            "Colunas esperadas não encontradas: "
            f"{colunas_faltantes}"
        )

    gdf_rms = gdf_rms[colunas].copy()

    # PostgreSQL criou os nomes em minúsculo
    gdf_rms.columns = [
        coluna.lower()
        for coluna in gdf_rms.columns
    ]

    print(
        "Validação concluída com sucesso: "
        "27 municípios da RMS."
    )

    return gdf_rms, quantidade_total


# ============================================================
# REGISTRAR INGESTÃO
# ============================================================

def registrar_ingestao(
    conexao,
    id_fonte: int,
    ano: int,
    nome_arquivo: str,
    hash_arquivo: str,
    quantidade_lida: int,
    quantidade_carregada: int,
) -> None:

    conexao.execute(
        text(
            """
            INSERT INTO controle_ingestao (
                id_fonte,
                co_periodo_referencia,
                ds_versao,
                no_arquivo_origem,
                dt_obtencao,
                dt_processamento,
                ds_hash_sha256,
                qt_registros_lidos,
                qt_registros_carregados,
                qt_registros_rejeitados,
                ds_status,
                ds_observacao
            )
            VALUES (
                :id_fonte,
                :periodo,
                :versao,
                :arquivo,
                CURRENT_DATE,
                :processamento,
                :hash,
                :lidos,
                :carregados,
                0,
                'CONCLUIDA',
                :observacao
            )
            """
        ),
        {
            "id_fonte": id_fonte,
            "periodo": str(ano),
            "versao": f"Malha Municipal {ano}",
            "arquivo": nome_arquivo,
            "processamento": datetime.now(),
            "hash": hash_arquivo,
            "lidos": quantidade_lida,
            "carregados": quantidade_carregada,
            "observacao": (
                "Malha de SP filtrada para os "
                "27 municípios da RMS."
            ),
        },
    )


# ============================================================
# CARGA NO POSTGRESQL / POSTGIS
# ============================================================

def carregar_banco(
    gdf_rms: gpd.GeoDataFrame,
    ano: int,
    hash_arquivo: str,
    quantidade_lida: int,
    nome_arquivo: str,
) -> None:

    print("Enviando dados para o Supabase/PostGIS...")

    tabela_temporaria = "_stg_ibge_municipios"

    with engine.begin() as conexao:

        id_fonte = obter_id_fonte(conexao)

        # ----------------------------------------------------
        # Tabela temporária de estágio
        # ----------------------------------------------------

        gdf_rms.to_postgis(
            name=tabela_temporaria,
            con=conexao,
            if_exists="replace",
            index=False,
            dtype={
                "geometry": Geometry(
                    geometry_type="MULTIPOLYGON",
                    srid=4674,
                )
            },
        )

        # ----------------------------------------------------
        # UPSERT
        # ----------------------------------------------------

        conexao.execute(
            text(
                f"""
                INSERT INTO ibge_municipios (
                    cd_mun,
                    nm_mun,
                    cd_rgi,
                    nm_rgi,
                    cd_rgint,
                    nm_rgint,
                    cd_uf,
                    nm_uf,
                    sigla_uf,
                    cd_regiao,
                    nm_regiao,
                    sigla_rg,
                    cd_concurb,
                    nm_concurb,
                    area_km2,
                    geometry
                )
                SELECT
                    cd_mun,
                    nm_mun,
                    cd_rgi,
                    nm_rgi,
                    cd_rgint,
                    nm_rgint,
                    cd_uf,
                    nm_uf,
                    sigla_uf,
                    cd_regiao,
                    nm_regiao,
                    sigla_rg,
                    cd_concurb,
                    nm_concurb,
                    area_km2,
                    geometry
                FROM {tabela_temporaria}

                ON CONFLICT (cd_mun)

                DO UPDATE SET
                    nm_mun = EXCLUDED.nm_mun,
                    cd_rgi = EXCLUDED.cd_rgi,
                    nm_rgi = EXCLUDED.nm_rgi,
                    cd_rgint = EXCLUDED.cd_rgint,
                    nm_rgint = EXCLUDED.nm_rgint,
                    cd_uf = EXCLUDED.cd_uf,
                    nm_uf = EXCLUDED.nm_uf,
                    sigla_uf = EXCLUDED.sigla_uf,
                    cd_regiao = EXCLUDED.cd_regiao,
                    nm_regiao = EXCLUDED.nm_regiao,
                    sigla_rg = EXCLUDED.sigla_rg,
                    cd_concurb = EXCLUDED.cd_concurb,
                    nm_concurb = EXCLUDED.nm_concurb,
                    area_km2 = EXCLUDED.area_km2,
                    geometry = EXCLUDED.geometry;
                """
            )
        )

        conexao.execute(
            text(
                f"DROP TABLE {tabela_temporaria};"
            )
        )

        registrar_ingestao(
            conexao=conexao,
            id_fonte=id_fonte,
            ano=ano,
            nome_arquivo=nome_arquivo,
            hash_arquivo=hash_arquivo,
            quantidade_lida=quantidade_lida,
            quantidade_carregada=len(gdf_rms),
        )

    print(
        "IBGE_MUNICIPIOS atualizada com sucesso."
    )


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

def executar_pipeline() -> None:

    print("")
    print("========================================")
    print("VELTIS - MALHA MUNICIPAL IBGE")
    print("========================================")
    print("")

    # 1. Descobrir versão
    ano = descobrir_ano_mais_recente()

    # 2. Baixar
    caminho_temporario, url = baixar_malha(ano)

    # 3. Calcular hash
    hash_arquivo = calcular_hash(
        caminho_temporario
    )

    print(
        f"SHA-256: {hash_arquivo}"
    )

    # 4. Verificar se já foi carregado
    with engine.begin() as conexao:

        id_fonte = obter_id_fonte(
            conexao
        )

        if hash_ja_processado(
            conexao,
            id_fonte,
            hash_arquivo,
        ):
            print("")
            print(
                "Essa versão já foi carregada anteriormente."
            )
            print(
                "Nenhuma atualização é necessária."
            )

            caminho_temporario.unlink(
                missing_ok=True
            )

            return

    # 5. Salvar arquivo oficial
    nome_zip = f"SP_Municipios_{ano}.zip"

    caminho_final = DATA_DIR / nome_zip

    caminho_temporario.replace(
        caminho_final
    )

    # 6. Extrair
    caminho_shp = extrair_malha(
        caminho_final,
        ano,
    )

    # 7. Processar e validar
    gdf_rms, quantidade_lida = (
        processar_malha(
            caminho_shp
        )
    )

    # 8. Carregar no banco
    carregar_banco(
        gdf_rms=gdf_rms,
        ano=ano,
        hash_arquivo=hash_arquivo,
        quantidade_lida=quantidade_lida,
        nome_arquivo=nome_zip,
    )

    print("")
    print("========================================")
    print("PIPELINE CONCLUÍDA")
    print("========================================")
    print("")


if __name__ == "__main__":
    executar_pipeline()