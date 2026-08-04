import pandas as pd
import psycopg2
import zipfile

# Conexão com o banco
conexao_string = ""

# Códigos dos 5 municípios da amostra
CODIGOS_RM = ['3552205', '3557006', '3523909', '3554003', '3550605']

# Colunas que vamos usar do CSV
COLUNAS = [
    'CO_ENTIDADE',      # código da escola
    'NO_ENTIDADE',      # nome da escola
    'CO_MUNICIPIO',     # código do município
    'TP_DEPENDENCIA',   # pública ou privada
    'DS_ENDERECO',      # endereço
    'NO_BAIRRO',        # bairro
    'CO_CEP',           # CEP
    'NU_TELEFONE',      # telefone
    'LATITUDE',         # latitude
    'LONGITUDE',        # longitude
    'TP_SITUACAO_FUNCIONAMENTO',  # ativa ou não
    'IN_COMUM_MEDIO_MEDIO'        # tem ensino médio?
]

# Mapa de dependência administrativa
DEPENDENCIA = {
    1: 'FEDERAL',
    2: 'ESTADUAL', 
    3: 'MUNICIPAL',
    4: 'PRIVADA'
}

print("📂 Lendo CSV do INEP...")

# Conecta no banco
conn = psycopg2.connect(conexao_string)
cursor = conn.cursor()

escolas_inseridas = 0
caminho_zip = "C:/Users/jmr94/Downloads/microdados_censo_escolar_2025_.zip"
arquivo_csv = "microdados_censo_escolar_2025/dados/Tabela_Escola_2025.csv"

# Abre o ZIP e lê o CSV em chunks
with zipfile.ZipFile(caminho_zip, 'r') as z:
    with z.open(arquivo_csv) as f:
        
        # Lê em pedaços de 10 mil linhas
        for chunk in pd.read_csv(f, sep=';', encoding='latin1', 
                                  usecols=COLUNAS, chunksize=10000,
                                  low_memory=False):
            
            # Filtra só os municípios da amostra
            chunk['CO_MUNICIPIO'] = chunk['CO_MUNICIPIO'].astype(str)
            filtrado = chunk[chunk['CO_MUNICIPIO'].isin(CODIGOS_RM)]
            
            # Filtra só escolas com ensino médio
            filtrado = filtrado[filtrado['IN_COMUM_MEDIO_MEDIO'] == 1]
            
            # Filtra só escolas ativas (situação 1 = ativa)
            filtrado = filtrado[filtrado['TP_SITUACAO_FUNCIONAMENTO'] == 1]
            
            # Pega no máximo 4 escolas por município (amostra)
            filtrado = filtrado.groupby('CO_MUNICIPIO').head(4)
            
            for _, row in filtrado.iterrows():
                
                # Trata latitude e longitude
                lat = float(row['LATITUDE']) if pd.notna(row['LATITUDE']) else None
                lng = float(row['LONGITUDE']) if pd.notna(row['LONGITUDE']) else None
                
                # Trata telefone
                tel = str(row['NU_TELEFONE']) if pd.notna(row['NU_TELEFONE']) else None
                
                cursor.execute("""
                    INSERT INTO instituicao (
                        codigo_ibge, codigo_inep, nome, tipo,
                        dependencia, endereco, bairro, cep,
                        telefone, latitude, longitude
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    str(row['CO_MUNICIPIO']),
                    str(row['CO_ENTIDADE']),
                    row['NO_ENTIDADE'],
                    'MEDIO',
                    DEPENDENCIA.get(int(row['TP_DEPENDENCIA']), 'PRIVADA'),
                    row['DS_ENDERECO'] if pd.notna(row['DS_ENDERECO']) else None,
                    row['NO_BAIRRO'] if pd.notna(row['NO_BAIRRO']) else None,
                    str(int(row['CO_CEP'])) if pd.notna(row['CO_CEP']) else None,
                    tel,
                    lat,
                    lng
                ))
                
                escolas_inseridas += 1
                print(f"   ✅ {row['NO_ENTIDADE']}")

conn.commit()
cursor.close()
conn.close()

print(f"\n🎉 {escolas_inseridas} escolas inseridas com sucesso!")