import pandas as pd
import psycopg2
import zipfile

# Conexão com o banco
conexao_string = ""

# Códigos dos 5 municípios da amostra
CODIGOS_RM = ['3552205', '3557006', '3523909', '3554003', '3550605']

# Caminho do ZIP do MEC
caminho_zip = "C:/Users/jmr94/Downloads/microdados_censo_da_educacao_superior_2024.zip"

# Mapa de organização acadêmica
ORGANIZACAO = {
    1: 'UNIVERSIDADE',
    2: 'CENTRO_UNIVERSITARIO',
    3: 'FACULDADE',
    4: 'IF_CEFET'
}

# Mapa de grau acadêmico
GRAU = {
    1: 'BACHARELADO',
    2: 'LICENCIATURA',
    3: 'TECNOLOGO'
}

# Mapa de modalidade
MODALIDADE = {
    1: 'PRESENCIAL',
    2: 'EAD'
}

print("Lendo arquivo de IES do MEC")

# Conecta no banco
conn = psycopg2.connect(conexao_string)
cursor = conn.cursor()

# =====================
# PASSO 1: Inserir IES
# =====================
with zipfile.ZipFile(caminho_zip, 'r') as z:
    with z.open('microdados_censo_da_educacao_superior_2024/dados/MICRODADOS_ED_SUP_IES_2024.CSV') as f:
        df_ies = pd.read_csv(f, sep=';', encoding='latin1', low_memory=False)
        
        # Filtra os municípios da amostra
        df_ies['CO_MUNICIPIO_IES'] = df_ies['CO_MUNICIPIO_IES'].astype(str)
        df_rm = df_ies[df_ies['CO_MUNICIPIO_IES'].isin(CODIGOS_RM)]
        
        # Pega 1 IES por município
        df_amostra = df_rm.groupby('CO_MUNICIPIO_IES').head(1)
        
        print(f"{len(df_amostra)} IES encontradas")
        print("Inserindo IES no banco...")
        
        for _, row in df_amostra.iterrows():
            cursor.execute("""
                INSERT INTO instituicao (
                    codigo_ibge, codigo_ies, nome, tipo,
                    dependencia, endereco, bairro, cep
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                str(row['CO_MUNICIPIO_IES']),
                int(row['CO_IES']),
                row['NO_IES'],
                'SUPERIOR',
                'PRIVADA' if row['TP_CATEGORIA_ADMINISTRATIVA'] in [4,5,6,7] else 'FEDERAL' if row['TP_CATEGORIA_ADMINISTRATIVA'] == 1 else 'ESTADUAL',
                row['DS_ENDERECO_IES'] if pd.notna(row['DS_ENDERECO_IES']) else None,
                row['NO_BAIRRO_IES'] if pd.notna(row['NO_BAIRRO_IES']) else None,
                str(int(row['NU_CEP_IES'])) if pd.notna(row['NU_CEP_IES']) else None
            ))
            print(f" {row['NO_IES']}")

conn.commit()
print("IES inseridas!")

# ========================
# PASSO 2: Inserir cursos
# ========================
print("\n Lendo arquivo de cursos do MEC...")

# Busca os IDs das IES 
cursor.execute("SELECT id, codigo_ies FROM instituicao WHERE tipo = 'SUPERIOR'")
ies_no_banco = {row[1]: row[0] for row in cursor.fetchall()}

co_ies_lista = list(ies_no_banco.keys())

with zipfile.ZipFile(caminho_zip, 'r') as z:
    with z.open('microdados_censo_da_educacao_superior_2024/dados/MICRODADOS_CADASTRO_CURSOS_2024.CSV') as f:
        
        cursos_inseridos = 0
        
        for chunk in pd.read_csv(f, sep=';', encoding='latin1',
                                  low_memory=False, chunksize=10000):
            
            # Filtra só cursos das IES 
            filtrado = chunk[chunk['CO_IES'].isin(co_ies_lista)]
            
            # Filtra só cursos ativos
            if 'TP_SITUACAO_CURSO' in filtrado.columns:
                filtrado = filtrado[filtrado['TP_SITUACAO_CURSO'] == 1]
            
            for _, row in filtrado.iterrows():
                
                # Pega o ID da instituição no banco
                inst_id = ies_no_banco.get(row['CO_IES'])
                if not inst_id:
                    continue
                
                grau = GRAU.get(int(row['TP_GRAU_ACADEMICO'])) if pd.notna(row['TP_GRAU_ACADEMICO']) else None
                modalidade = MODALIDADE.get(int(row['TP_MODALIDADE_ENSINO'])) if pd.notna(row['TP_MODALIDADE_ENSINO']) else None
                vagas = int(row['QT_VG_TOTAL']) if pd.notna(row['QT_VG_TOTAL']) else None
                
                cursor.execute("""
                    INSERT INTO curso (
                        instituicao_id, nome, nivel,
                        grau, modalidade, vagas_anuais
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    inst_id,
                    row['NO_CURSO'],
                    'SUPERIOR',
                    grau,
                    modalidade,
                    vagas
                ))
                
                cursos_inseridos += 1

conn.commit()
cursor.close()
conn.close()

print(f" {cursos_inseridos} cursos inseridos com sucesso!")
print("\n Script de ensino superior finalizado!")