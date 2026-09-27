# Veltis

O **Veltis** é um Projeto Integrador acadêmico voltado à integração de dados públicos oficiais da Região Metropolitana de Sorocaba (RMS), composta por 27 municípios.

## Objetivo

Reunir e organizar dados territoriais, demográficos e educacionais em uma estrutura única, permitindo futuramente consultas, filtros, mapas, indicadores e visualizações web.

## Estado atual

### Implementado
- PostgreSQL/PostGIS inicial.
- Conexão Python com PostgreSQL.
- Leitura e validação da Malha Municipal do IBGE.
- Filtro dos 27 municípios da RMS.
- Carga inicial dos municípios no PostGIS.

### Em desenvolvimento
- Coletores automáticos por fonte.
- Integração SIDRA/IBGE.
- Censo Escolar e cursos técnicos.
- Localização de escolas a partir de fontes complementares oficiais.
- Censo da Educação Superior.

### Planejado
- FastAPI.
- React.
- Mapa interativo.
- Filtros, indicadores e dashboards.

## Estrutura

```text
backend/
├── data/
│   ├── raw/          # dados oficiais brutos; não versionados
│   └── processed/    # saídas intermediárias; não versionadas
├── src/
│   ├── collectors/   # um coletor por fonte
│   ├── config/       # configurações compartilhadas, como os 27 códigos RMS
│   ├── validators/   # validações reutilizáveis
│   ├── transforms/   # transformações reutilizáveis
│   ├── loaders/      # carga no PostgreSQL/PostGIS
│   └── database.py   # conexão com o banco
└── requirements.txt

docs/                 # documentação técnica atual do projeto
frontend/             # reservado para a aplicação React futura
```

## Fontes previstas/utilizadas
- IBGE — Malha Municipal.
- IBGE — SIDRA / API de Dados Agregados.
- INEP — Censo Escolar.
- INEP — Catálogo de Escolas.
- SEDUC-SP — fonte complementar de localização.
- INEP — Censo da Educação Superior.

## Configuração local

Crie o ambiente virtual e instale as dependências:

```bash
cd backend
python -m venv .venv
```

Ative o ambiente e execute:

```bash
pip install -r requirements.txt
```

Copie `.env.example` para `.env` e informe a `DATABASE_URL` do PostgreSQL/Supabase.

> Credenciais e arquivos `.env` nunca devem ser enviados ao GitHub.

## Dados brutos

Arquivos oficiais baixados de IBGE, INEP e demais fontes não são versionados no Git. Eles ficam em `backend/data/raw/` e devem ser obtidos pelos coletores ou pelo procedimento documentado para cada fonte.
