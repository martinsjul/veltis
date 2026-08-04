import requests
import psycopg2

# Conexão com o banco
conexao_string = ""

# Códigos dos 5 municípios da amostra
CODIGOS = "3552205,3557006,3523909,3554003,3550605"

def buscar_variavel(tabela, variavel, ano="2022"):
    """
    Função que busca uma variável específica na API SIDRA do IBGE.
    Recebe o número da tabela, o código da variável e o ano.
    Devolve um dicionário com código IBGE → valor.
    """
    url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/periodos/{ano}/variaveis/{variavel}?localidades=N6[{CODIGOS}]"
    
    print(f"   🌐 Consultando API: tabela {tabela}, variável {variavel}...")
    
    resposta = requests.get(url)
    dados = resposta.json()
    
    resultado = {}
    for item in dados[0]['resultados'][0]['series']:
        codigo = item['localidade']['id']
        valor = item['serie'][ano]
        resultado[codigo] = valor
    
    return resultado

print("🌐 Buscando dados demográficos na API SIDRA do IBGE...")

# Busca população total — tabela 9514, variável 93
populacao = buscar_variavel("9514", "93")
print(f"✅ População coletada para {len(populacao)} municípios")

# Conecta no banco
conn = psycopg2.connect(conexao_string)
cursor = conn.cursor()

print("📥 Inserindo dados demográficos no banco...")

for codigo, pop in populacao.items():
    # Trata valores que podem vir como string ou como "-"
    pop_valor = int(pop) if pop not in ["-", "..."] else None
    
    cursor.execute("""
        INSERT INTO demografico (
            codigo_ibge,
            ano_referencia,
            populacao_total
        )
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (
        codigo,
        2022,
        pop_valor
    ))
    
    print(f"   ✅ {codigo}: {pop_valor} habitantes")

conn.commit()
cursor.close()
conn.close()

print("🎉 Dados demográficos inseridos com sucesso!")