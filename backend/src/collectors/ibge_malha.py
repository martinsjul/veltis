"""Pipeline 1 - IBGE Malha Municipal -> IBGE_MUNICIPIOS.

Baixa o shapefile oficial de SP, recorta os 27 municípios da RMS,
valida (quantidade, códigos, CRS, geometrias) e grava com upsert.

Executar sozinho:  python -m src.collectors.ibge_malha [--forcar]
"""

import argparse
import shutil
import zipfile
from pathlib import Path

import geopandas as gpd
from shapely.geometry import MultiPolygon

from src.collectors.download import baixar_arquivo
from src.config.edicoes import ANO_MALHA, URL_MALHA, URL_PAGINA_MALHA
from src.config.rms import CODIGOS_RMS
from src.loaders.carga import para_registros, upsert
from src.loaders.ingestao import Fonte, carga, hash_arquivo


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "raw" / "ibge"

FONTE = Fonte(
    orgao="IBGE",
    nome="Malha Municipal",
    url_oficial=URL_PAGINA_MALHA,
    periodicidade="Anual",
    observacao="Malha territorial oficial utilizada pelo Veltis.",
)

COLUNAS = [
    "CD_MUN", "NM_MUN", "CD_RGI", "NM_RGI", "CD_RGINT", "NM_RGINT",
    "CD_UF", "NM_UF", "SIGLA_UF", "CD_REGIAO", "NM_REGIAO", "SIGLA_RG",
    "CD_CONCURB", "NM_CONCURB", "AREA_KM2", "geometry",
]


# ============================================================
# EXTRAÇÃO
# ============================================================

def extrair_malha(caminho_zip: Path, ano: int) -> Path:
    pasta = DATA_DIR / f"municipios_{ano}"

    if pasta.exists():
        shutil.rmtree(pasta)

    pasta.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(caminho_zip) as arquivo_zip:
        arquivo_zip.extractall(pasta)

    shapefiles = list(pasta.rglob("*.shp"))

    if len(shapefiles) != 1:
        raise RuntimeError(
            f"Era esperado exatamente 1 arquivo SHP, mas foram encontrados {len(shapefiles)}."
        )

    return shapefiles[0]


# ============================================================
# PROCESSAMENTO E VALIDAÇÃO (mesmas regras da versão original)
# ============================================================

def processar_malha(caminho_shp: Path) -> tuple[gpd.GeoDataFrame, int]:
    gdf = gpd.read_file(caminho_shp)
    quantidade_total = len(gdf)

    print(f"Municípios no arquivo de SP: {quantidade_total}")

    if "CD_MUN" not in gdf.columns:
        raise ValueError("A coluna CD_MUN não existe no arquivo.")

    gdf["CD_MUN"] = gdf["CD_MUN"].astype(str).str.strip()
    gdf_rms = gdf[gdf["CD_MUN"].isin(CODIGOS_RMS)].copy()

    if len(gdf_rms) != 27:
        raise ValueError(
            f"A RMS deve possuir exatamente 27 municípios. Foram encontrados {len(gdf_rms)}."
        )

    faltantes = set(CODIGOS_RMS) - set(gdf_rms["CD_MUN"])
    if faltantes:
        raise ValueError(f"Municípios da RMS não encontrados: {sorted(faltantes)}")

    if gdf_rms["CD_MUN"].duplicated().any():
        raise ValueError("Foram encontrados códigos de município duplicados.")

    if gdf_rms.crs is None:
        raise ValueError("O arquivo não possui CRS definido.")

    if gdf_rms.crs.to_epsg() != 4674:
        print(f"Convertendo CRS {gdf_rms.crs} para EPSG:4674...")
        gdf_rms = gdf_rms.to_crs(epsg=4674)

    if gdf_rms.geometry.isna().any():
        raise ValueError("Existem municípios sem geometria.")
    if gdf_rms.geometry.is_empty.any():
        raise ValueError("Existem geometrias vazias.")
    if not gdf_rms.geometry.is_valid.all():
        raise ValueError("Existem geometrias inválidas.")

    gdf_rms["geometry"] = gdf_rms.geometry.apply(
        lambda g: MultiPolygon([g]) if g.geom_type == "Polygon" else g
    )

    faltando_colunas = [c for c in COLUNAS if c not in gdf_rms.columns]
    if faltando_colunas:
        raise ValueError(f"Colunas esperadas não encontradas: {faltando_colunas}")

    gdf_rms = gdf_rms[COLUNAS].copy()
    gdf_rms.columns = [c.lower() for c in gdf_rms.columns]

    # Campos de texto vazios na fonte (ex.: concentração urbana) viram NULL.
    for coluna in gdf_rms.columns:
        if coluna not in ("geometry", "area_km2"):
            gdf_rms[coluna] = gdf_rms[coluna].map(
                lambda v: None if v is None or str(v).strip() == "" else str(v).strip()
            )

    print("Validação concluída: 27 municípios da RMS.")
    return gdf_rms, quantidade_total


# ============================================================
# CARGA
# ============================================================

def carregar_banco(ing, gdf_rms: gpd.GeoDataFrame) -> int:
    tabela = gdf_rms.drop(columns="geometry").copy()

    # A geometria vai como WKB em hexadecimal; o PostGIS reconstrói.
    # Isso dispensa a tabela de estágio no schema público.
    tabela["geometry"] = gdf_rms.geometry.to_wkb(hex=True)
    tabela["id_ingestao"] = ing.id_ingestao

    return upsert(
        ing.conexao,
        "ibge_municipios",
        para_registros(tabela),
        chave=["cd_mun"],
        expressoes={
            "geometry": "ST_Multi(ST_SetSRID(ST_GeomFromWKB(decode(:geometry, 'hex')), 4674))",
        },
    )


# ============================================================
# PIPELINE
# ============================================================

def executar_pipeline(forcar: bool = False) -> None:
    print("\n=== IBGE - MALHA MUNICIPAL ===")

    nome_zip = f"SP_Municipios_{ANO_MALHA}.zip"
    caminho_zip = baixar_arquivo(URL_MALHA, DATA_DIR / nome_zip, forcar=forcar)
    hash_ = hash_arquivo(caminho_zip)

    with carga(
        FONTE,
        periodo=str(ANO_MALHA),
        versao=f"Malha Municipal {ANO_MALHA}",
        arquivo=nome_zip,
        hash_arquivo=hash_,
        forcar=forcar,
    ) as ing:
        if ing is None:
            return

        caminho_shp = extrair_malha(caminho_zip, ANO_MALHA)
        gdf_rms, quantidade_lida = processar_malha(caminho_shp)
        carregados = carregar_banco(ing, gdf_rms)

        ing.registrar_contagens(
            lidos=quantidade_lida,
            carregados=carregados,
            observacao="Malha de SP filtrada para os 27 municípios da RMS.",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--forcar", action="store_true", help="recarrega mesmo sem mudança")
    executar_pipeline(forcar=parser.parse_args().forcar)
