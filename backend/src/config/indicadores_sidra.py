"""Indicadores do SIDRA carregados no Veltis.

Cada item vira uma consulta à API v3 do IBGE para os 27 municípios.
As categorias são pedidas de forma EXPLÍCITA: o parâmetro [all]
mistura níveis (grupos de idade e idades simples) e faz contar em dobro.

Nas tabelas do Censo 2022 o "Total" NÃO tem id 0; cada tabela tem o
seu (ex.: Sexo Total = 6794 na 9514). Códigos conferidos em
/api/v3/agregados/{tabela}/metadados em outubro de 2026.

Para incluir um indicador novo, acrescente um item nesta lista.
"""

# Grupos de 5 anos da classificação 287 (Idade) da tabela 9514, mais o Total.
_IDADE_9514_GRUPOS = [
    "100362",  # Total
    "93070", "93084", "93085", "93086", "93087", "93088", "93089",
    "93090", "93091", "93092", "93093", "93094", "93095", "93096",
    "93097", "93098", "49108", "49109", "60040", "60041", "6653",
]

INDICADORES_SIDRA = [
    {
        "agregado": "4709",
        "periodos": ["2022"],
        "variaveis": ["93", "10605"],
        "classificacoes": {},
        "descricao": "População residente 2022 e taxa de crescimento 2010-2022",
    },
    {
        "agregado": "4714",
        "periodos": ["2022"],
        "variaveis": ["6318", "614"],
        "classificacoes": {},
        "descricao": "Área territorial e densidade demográfica",
    },
    {
        "agregado": "6579",
        "periodos": ["2024", "2025", "2026"],
        "variaveis": ["9324"],
        "classificacoes": {},
        "descricao": "População residente estimada",
    },
    {
        "agregado": "9514",
        "periodos": ["2022"],
        "variaveis": ["93"],
        "classificacoes": {
            "2": ["6794", "4", "5"],      # Sexo: Total, Homens, Mulheres
            "287": _IDADE_9514_GRUPOS,    # Idade: Total + grupos de 5 anos
        },
        "descricao": "População por sexo e grupo de idade",
    },
    {
        "agregado": "9542",
        "periodos": ["2022"],
        "variaveis": ["950"],
        "classificacoes": {
            # Alfabetização: Total, Alfabetizadas, Não alfabetizadas
            "59": ["93024", "1023", "1024"],
        },
        "descricao": "Pessoas de 15 anos ou mais por alfabetização",
    },
    {
        "agregado": "10056",
        "periodos": ["2022"],
        "variaveis": ["3795"],
        "classificacoes": {
            # Grupo de idade: Total, 0-3, 4-5, 6-14, 15-17, 18-24, 25+
            "58": ["95253", "99749", "47813", "31615", "2792", "100052", "108866"],
        },
        "descricao": "Taxa bruta de frequência escolar por grupo de idade",
    },
    {
        "agregado": "10061",
        "periodos": ["2022"],
        "variaveis": ["2667"],
        "classificacoes": {
            # Nível de instrução: Total, Sem instrução/fund. incompleto,
            # Fund. completo/médio incompleto, Médio completo/sup. incompleto,
            # Superior completo
            "1568": ["120704", "9493", "9494", "9495", "99713"],
        },
        "descricao": "Pessoas de 18 anos ou mais por nível de instrução",
    },
]
