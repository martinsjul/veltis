import geopandas as gpd
import psycopg2
from shapely.geometry import mapping
import json

# Conexão com o banco
conexao_string = ""

# Os 5 municípios da amostra
MUNICIPIOS_AMOSTRA = {
    '3552205': 'Sorocaba',
    '3557006': 'Votorantim',
    '3523909': 'Itu',
    '3554003': 'Tatuí',
    '3550605': 'São Roque'
}

print("Lendo Shapefile do IBGE")

# Lê o shapefile direto do ZIP
gdf = gpd.read_file(
    "zip://C:/Users/jmr94/Downloads/SP_Municipios_2025.zip!SP_Municipios_2025.shp"
)

print(f"{len(gdf)} municípios carregados do estado de SP")

# Filtra só os 5 da amostra
gdf_amostra = gdf[gdf['CD_MUN'].isin(MUNICIPIOS_AMOSTRA.keys())]

print(f"{len(gdf_amostra)} municípios da amostra filtrados")

# Conecta no banco
conn = psycopg2.connect(conexao_string)
cursor = conn.cursor()

print(" Inserindo municípios no banco")

for _, row in gdf_amostra.iterrows():
    # Converte o polígono para GeoJSON
    geom_geojson = json.dumps(mapping(row.geometry))
    
    cursor.execute("""
        INSERT INTO municipio (codigo_ibge, nome, area_km2, poligono)
        VALUES (
            %s, %s, %s,
           ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
        )
        ON CONFLICT (codigo_ibge) DO NOTHING
    """, (
        row['CD_MUN'],
        row['NM_MUN'],
        round(float(row['AREA_KM2']), 2),
        geom_geojson
    ))
    
    print(f"  {row['NM_MUN']} inserido")

# Salva tudo no banco
conn.commit()

cursor.close()
conn.close()

print(" Municípios importados com sucesso!")