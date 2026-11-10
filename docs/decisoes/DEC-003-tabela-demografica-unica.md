# DEC-003 — Tabela demográfica única

- **Estado:** aceita (aprovada pelo orientador, prof. Munari, em 2026-10-26)
- **Data:** 2026-10-19 (proposta) / 2026-10-26 (aprovação)
- **Responsáveis pela decisão:** equipe do projeto e orientador
- **Relacionado a:** migration `002_integridade_e_demografico.sql`; pipeline `sidra`; `vw_indicadores_municipio`

## Contexto

O modelo inicial separava os valores do IBGE em duas tabelas: `IBGE_DEMOGRAFICO` (o número) e `IBGE_DEMO_CLASSIF` (as classificações, como sexo e faixa de idade). Na prática só a primeira recebia dados, e o orientador pediu que a demografia ficasse em uma tabela só.

No SIDRA, o mesmo indicador aparece várias vezes com classificações diferentes (por exemplo, população total, homens, mulheres e cada faixa de idade). A classificação faz parte do significado do valor.

## Alternativas consideradas

- **Manter duas tabelas (valor + classificação):** normalizado, mas exige junções para qualquer consulta e não estava sendo usado.
- **Uma coluna por classificação conhecida (sexo, idade...):** simples de ler, mas cada tabela do SIDRA tem classificações diferentes e o esquema mudaria a cada indicador novo.
- **Uma tabela, com a classificação na própria linha:** uma chave textual curta e ordenada (`DS_CHAVE_CLASSIFICACAO`, ex.: `2:4|286:113635|287:100362`) e o detalhe legível em JSON (`JS_CLASSIFICACOES`).

## Decisão e justificativa

Opção 3. `IBGE_DEMOGRAFICO` guarda um valor por linha, com município, período, tabela (agregado), variável e a classificação. A unicidade é garantida por `UNIQUE (CD_MUN, CO_PERIODO, CD_AGREGADO, CD_VARIAVEL, DS_CHAVE_CLASSIFICACAO)`. A tabela `IBGE_DEMO_CLASSIF` foi removida na migration 002, que só executa se ela estiver vazia.

## Consequências e revisão

- Um indicador novo do SIDRA entra só com configuração (`src/config/indicadores_sidra.py`), sem mudar o banco.
- Consultas por classificação usam a chave textual ou o índice GIN no JSON.
- A `vw_indicadores_municipio` monta uma linha por município para o frontend.
- Revisar se o volume crescer a ponto de a consulta por JSON ficar lenta.
