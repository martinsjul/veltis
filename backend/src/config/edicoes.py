"""Edições fixas de cada fonte.

Os coletores carregam SEMPRE a edição definida aqui, nunca
"a mais recente". Assim, rodar o pipeline daqui a um ano produz
o mesmo banco. Para atualizar uma fonte, mude o ano aqui, rode o
pipeline e atualize o dicionário de dados.
"""

# IBGE - Malha Municipal (shapefile de SP)
ANO_MALHA = 2025
URL_MALHA = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    f"malhas_municipais/municipio_{ANO_MALHA}/UFs/SP/SP_Municipios_{ANO_MALHA}.zip"
)
URL_PAGINA_MALHA = (
    "https://www.ibge.gov.br/geociencias/organizacao-do-territorio/"
    "estrutura-territorial/15774-malhas"
)

# INEP - Censo Escolar (edição 2025 V2, publicada em julho de 2026)
ANO_CENSO_ESCOLAR = 2025
URL_PAGINA_CENSO_ESCOLAR = (
    "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/"
    "microdados/censo-escolar"
)
# Atenção: a URL oficial de 2025 termina com "_" antes do .zip.
URL_CENSO_ESCOLAR = (
    "https://download.inep.gov.br/dados_abertos/"
    f"microdados_censo_escolar_{ANO_CENSO_ESCOLAR}_.zip"
)

# INEP - Censo da Educação Superior
# A edição 2025 está prevista para "até 30/11/2026".
ANO_CENSO_SUPERIOR = 2024
URL_PAGINA_CENSO_SUPERIOR = (
    "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/"
    "microdados/censo-da-educacao-superior"
)
URL_CENSO_SUPERIOR = (
    "https://download.inep.gov.br/microdados/"
    f"microdados_censo_da_educacao_superior_{ANO_CENSO_SUPERIOR}.zip"
)

# Fontes complementares de localização (arquivos colocados à mão em data/raw)
URL_CATALOGO_ESCOLAS = (
    "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/"
    "inep-data/catalogo-de-escolas/"
)
URL_SEDUC_ESCOLAS = "https://dados.educacao.sp.gov.br/dataset/escolas-ativas"

# IBGE - SIDRA / API de Dados Agregados v3
URL_SIDRA = "https://servicodados.ibge.gov.br/api/v3/agregados"
