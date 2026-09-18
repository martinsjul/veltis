from pathlib import Path
import sys

import geopandas as gpd


BASE_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = BASE_DIR / "src"

sys.path.append(str(SRC_DIR))

from database import engine


CAMINHO_ARQUIVO = (
    BASE_DIR
    / "data"
    / "raw"
    / "ibge"
    / "SP_Municipios_2025.shp"
)

CODIGOS_RMS = [
    "3500758",  # Alambari
    "3501152",  # Alumínio
    "3502754",  # Araçariguama
    "3502903",  # Araçoiaba da Serra
    "3507001",  # Boituva
    "3510302",  # Capela do Alto
    "3511508",  # Cerquilho
    "3511607",  # Cesário Lange
    "3519709",  # Ibiúna
    "3521002",  # Iperó
    "3522307",  # Itapetininga
    "3523909",  # Itu
    "3525854",  # Jumirim
    "3528403",  # Mairinque
    "3537800",  # Piedade
    "3537909",  # Pilar do Sul
    "3540606",  # Porto Feliz
    "3545209",  # Salto
    "3545308",  # Salto de Pirapora
    "3550209",  # São Miguel Arcanjo
    "3550605",  # São Roque
    "3551108",  # Sarapuí
    "3552205",  # Sorocaba
    "3553500",  # Tapiraí
    "3554003",  # Tatuí
    "3554508",  # Tietê
    "3557006",  # Votorantim
]


gdf = gpd.read_file(CAMINHO_ARQUIVO)


gdf["CD_MUN"] = gdf["CD_MUN"].astype(str)


gdf_rms = gdf[
    gdf["CD_MUN"].isin(CODIGOS_RMS)
].copy()


print("\nMunicípios encontrados:")

print(
    gdf_rms[
        ["CD_MUN", "NM_MUN"]
    ].sort_values("NM_MUN")
)


print("\nQuantidade encontrada:")
print(len(gdf_rms))

if len(gdf_rms) != 27:
    raise ValueError(
        f"Esperávamos 27 municípios, "
        f"mas foram encontrados {len(gdf_rms)}."
    )


codigos_encontrados = set(gdf_rms["CD_MUN"])

codigos_faltantes = (
    set(CODIGOS_RMS)
    - codigos_encontrados
)

if codigos_faltantes:
    raise ValueError(
        f"Códigos não encontrados: {codigos_faltantes}"
    )

if gdf_rms.crs is None:
    raise ValueError(
        "O arquivo não possui CRS definido."
    )

print("\nCRS encontrado:")
print(gdf_rms.crs)

if gdf_rms.crs.to_epsg() != 4674:
    print("\nConvertendo CRS para EPSG:4674...")

    gdf_rms = gdf_rms.to_crs(
        epsg=4674
    )


print("\nValores nulos por coluna:")
print(gdf_rms.isnull().sum())


print("\nGeometrias válidas:")
print(
    gdf_rms.geometry.is_valid.value_counts()
)

print("\nGeometrias vazias:")
print(
    gdf_rms.geometry.is_empty.value_counts()
)

if gdf_rms.geometry.isna().any():
    raise ValueError(
        "Existem municípios sem geometria."
    )

if not gdf_rms.geometry.is_valid.all():
    raise ValueError(
        "Existem geometrias inválidas."
    )

if gdf_rms.geometry.is_empty.any():
    raise ValueError(
        "Existem geometrias vazias."
    )


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

gdf_rms = gdf_rms[colunas]

gdf_rms.columns = [
    coluna.lower()
    for coluna in gdf_rms.columns
]

gdf_rms.to_postgis(
    name="ibge_municipios",
    con=engine,
    if_exists="append",
    index=False,
)
print(
    "\n27 municípios inseridos no banco com sucesso!"
)