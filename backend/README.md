# Backend — banco de dados, pipelines e API

Guia técnico do backend do Veltis. A apresentação do projeto está no [README principal](../README.md).

## Responsabilidade e limites

- **Responsabilidade:** coletar, validar e carregar os dados oficiais (IBGE, INEP, SEDUC-SP) num PostgreSQL/PostGIS e expô-los por uma API de leitura.
- **Interfaces/consumidores:** portal web (`frontend/`). A API não grava dados; as cargas são feitas só pelos pipelines.
- **Estado atual:** disponível. Banco carregado e verificado em 2026-10-19; API testada contra o Supabase em 2026-10-26; coordenadas das faculdades e geocodificação das escolas implementadas em 2026-11-03 e carregadas no Supabase em 2026-11-06.

## Pré-requisitos

| Dependência | Versão suportada | Como verificar |
| --- | --- | --- |
| Python | 3.11 ou mais novo (testado no 3.13) | `python --version` |
| PostgreSQL + PostGIS | PostgreSQL 16/17 com PostGIS 3 (produção: Supabase, PostgreSQL 17.6 + PostGIS 3.3) | `SELECT postgis_full_version();` |
| Bibliotecas Python | versões fixas em `requirements.txt` | `pip list` |
| Espaço em disco | ~1 GB no cache do usuário para o CNEFE (etapa `geocodificacao`) e ~1 GB em `data/raw` para os pacotes do INEP | — |

## Configuração local

1. Copie `.env.example` para `.env` (dentro de `backend/`).
2. Preencha a conexão do banco. Nunca envie o `.env` ao GitHub (ele está no `.gitignore`).
3. Para testes de integração, use um banco **vazio e descartável**, nunca o Supabase.

| Variável | Obrigatória? | Formato (exemplo fictício) | Uso |
| --- | --- | --- | --- |
| `DATABASE_URL` | sim | `postgresql+psycopg://USUARIO:SENHA@HOST:5432/postgres?sslmode=require` | Conexão dos pipelines e da API |
| `VELTIS_CORS_ORIGENS` | não | `http://localhost:5173,https://veltis.exemplo.com` | Endereços do frontend autorizados a chamar a API |
| `VELTIS_TESTE_DATABASE_URL` | não | `postgresql+psycopg://postgres:senha@localhost:5432/veltis_teste` | Testes de integração do banco |
| `VELTIS_TESTE_API` | não | `1` | Liga os testes da API contra o banco do `.env` |

## Instalar, executar e testar

```text
Instalação:      python -m venv .venv  →  ativar  →  pip install -r requirements.txt
Migrations:      python -m src.migrar
Pipelines:       python -m src.pipeline            (ou --apenas <etapa>, --forcar, --verificar)
API:             uvicorn api.main:app --reload     → http://127.0.0.1:8000/docs
Testes:          pytest
```

Última execução verificada: 2026-11-03, Python 3.13, banco local com dados do INEP/IBGE — 80 testes unitários, 6 de integração do banco e 30 da API passaram (detalhes em [`docs/testes/`](../docs/testes/plano-e-evidencias-de-testes.md)).

## API e erros

Contrato OpenAPI em `/openapi.json` e documentação interativa em `/docs` com a API ligada. Não há autenticação: os dados são públicos e a API é somente de leitura. Respostas de erro: `404` (item inexistente), `422` (filtro inválido), `503` (banco indisponível, sem detalhes técnicos). Guia para o frontend: [`docs/uso interno/GUIA_API_PARA_O_FRONTEND.md`](../docs/uso%20interno/GUIA_API_PARA_O_FRONTEND.md).

## Vínculo com a documentação do projeto

- **Modelagem de dados e DER:** [`docs/dados/`](../docs/dados/README.md)
- **Arquitetura e diagrama de classes:** [`docs/arquitetura/`](../docs/arquitetura/README.md)
- **Plano de testes e evidências:** [`docs/testes/`](../docs/testes/plano-e-evidencias-de-testes.md)
- **Decisões:** [`docs/decisoes/`](../docs/decisoes/README.md)

---

## Fontes e tabelas

| # | Etapa (`--apenas`) | Fonte oficial | Edição | Tabelas |
| --- | --- | --- | --- | --- |
| 1 | `malha` | IBGE, Malha Municipal | 2025 | `ibge_municipios` |
| 2 | `sidra` | IBGE, SIDRA (API v3) | Censo 2022 + estimativas 2024–2026 | `ibge_demografico` |
| 3 | `censo_escolar` | INEP, Censo Escolar | 2025 V2 | `inep_escola`, `inep_curso_tecnico` |
| 4 | `localizacao` | INEP Catálogo de Escolas + SEDUC-SP | exportação manual | `escola_localizacao` |
| 5 | `geocodificacao` | IBGE CNEFE 2022 via geocodebr (Ipea) | Censo 2022 | `escola_localizacao` (só escolas sem ponto oficial) |
| 6 | `censo_superior` | INEP, Censo da Educação Superior | 2024 | `mec_ies`, `mec_cursos` |
| 7 | `locais_ies` | Levantamento dos campi (endereço oficial + OpenStreetMap) | arquivo versionado | `ies_local_oferta` |

Toda carga fica registrada em `fonte_dados` e `controle_ingestao`: arquivo, hash SHA-256, contagens e status (`INICIADA`, `CONCLUIDA` ou `FALHA`). Cada linha de dados guarda o `id_ingestao` da carga que a gerou.

As edições ficam fixas em `backend/src/config/edicoes.py`. Rodar de novo produz o mesmo banco; para atualizar uma fonte, mude o ano ali.

## Estrutura

```text
backend/
├── api/                   API FastAPI (só leitura das views)
│   ├── main.py            cria a aplicação, CORS, compressão e erros
│   ├── rotas/             mapa, municipios, escolas, cursos, gerais (filtros, fontes, saúde)
│   ├── modelos.py         formato das respostas (aparece no /docs)
│   └── db.py, filtros.py, geojson.py, dominios.py, config.py
├── database/migrations/   001 schema · 002 integridade + demografia · 003 views · 004 locais das faculdades · 005 geocodificação
├── certs/                 certificado intermediário do INEP (ver "Download do INEP")
├── data/
│   ├── raw/               arquivos oficiais (não versionados)
│   │   ├── ibge/  inep/censo_escolar/  inep/censo_superior/   ← baixados automaticamente
│   │   └── inep/catalogo_escolas/  seduc_sp/                  ← colocados à mão
│   ├── processed/
│   └── referencia/        ies_locais_oferta.csv: coordenadas dos campi (versionado)
├── src/
│   ├── config/            27 códigos da RMS, edições, indicadores SIDRA, colunas de localização
│   ├── collectors/        um coletor por fonte + download.py
│   ├── transforms/        conversões (códigos, 0/1 → booleano, valores do SIDRA)
│   ├── validators/        validações (recorte RMS, colunas, duplicidade, domínios)
│   ├── loaders/           ingestao.py (controle de cargas) e carga.py (upsert em lote)
│   ├── database.py        conexão (criada sob demanda)
│   ├── migrar.py          aplica as migrations
│   ├── pipeline.py        roda todos os coletores na ordem
│   └── verificar.py       relatório de qualidade do banco
├── tests/
└── requirements.txt
docs/                      casos de uso, dados (DER e dicionário), requisitos, decisões e guias de uso interno
frontend/                  aplicação React (próxima fase)
```

## Detalhes de configuração

Requer Python 3.11 ou mais novo.

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    |    Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

Copie `.env.example` para `.env` e informe a `DATABASE_URL`. Depois teste a conexão:

```bash
python teste_conexao.py
```

> Credenciais e arquivos `.env` nunca devem ser enviados ao GitHub.

## Banco de dados: migrations

```bash
python -m src.migrar --status     # o que já foi aplicado
python -m src.migrar              # aplica as pendentes, uma transação por arquivo
```

**No Supabase atual, que foi criado à mão com o script da migration 001:**

1. Faça um backup (Supabase → Database → Backups, ou `pg_dump`).
2. Registre a 001 como já aplicada, sem executá-la:
   `python -m src.migrar --marcar-aplicada 001_schema_inicial.sql`
3. Aplique as demais: `python -m src.migrar`

A migration 002 preserva os dados já carregados. Antes de alterar qualquer coisa, ela confere três pontos e para sem mudar nada se algum falhar:

- `ibge_demo_classif` está vazia;
- não há fontes duplicadas;
- não há valores do SIDRA duplicados.

### O que a migration 002 muda

- `ibge_demografico` passa a ser a **tabela demográfica única**. As classificações (sexo, idade e outras) ficam na própria linha, nas colunas `ds_chave_classificacao` e `js_classificacoes`. A tabela `ibge_demo_classif` é removida.
- **Chaves únicas** impedem duplicidade em `fonte_dados`, `ibge_demografico` e `mec_cursos`.
- A coluna `id_ingestao` entra em todas as tabelas de dados.
- **RLS ligado** em todas as tabelas. A API automática do Supabase (chave anon) não lê nem altera nada; o backend usa a conexão direta.

## Rodando os pipelines

```bash
python -m src.pipeline                        # tudo, na ordem certa, e no fim a verificação
python -m src.pipeline --apenas sidra         # uma etapa
python -m src.pipeline --forcar               # recarrega mesmo que a fonte não tenha mudado
python -m src.pipeline --verificar            # só o relatório de qualidade
```

Rodar duas vezes não duplica nada: o hash do arquivo decide se é preciso recarregar, e a gravação é por upsert. Se uma etapa falhar, as seguintes não rodam, e o erro fica gravado em `controle_ingestao` com status `FALHA`.

Os pacotes do INEP são grandes (Censo Escolar ≈ 537 MB, Censo Superior ≈ 457 MB). Eles são baixados uma vez para `data/raw` e reaproveitados depois.

### Localização das escolas (arquivos manuais)

O Catálogo de Escolas do INEP e a base da SEDUC-SP não têm download automático:

1. Exporte o Catálogo de Escolas (filtro SP) e salve o CSV ou XLSX em `backend/data/raw/inep/catalogo_escolas/`.
2. Baixe o arquivo de endereços de [Escolas Ativas da SEDUC-SP](https://dados.educacao.sp.gov.br/dataset/escolas-ativas) e salve em `backend/data/raw/seduc_sp/`.
3. Rode `python -m src.pipeline --apenas localizacao`.

O coletor reconhece as colunas pelo nome, ignorando acentos e maiúsculas. Se ele não achar uma coluna, a mensagem mostra o cabeçalho do arquivo; acrescente o nome em `src/config/fontes_localizacao.py`. Sem esses arquivos, a etapa é pulada com um aviso.

### Geocodificação das escolas sem coordenada

A etapa `geocodificacao` calcula o ponto das escolas que têm endereço mas não têm coordenada oficial, usando o [geocodebr](https://github.com/ipea/geocodebr) (Ipea) sobre o CNEFE do IBGE. É gratuita e roda no próprio computador.

- Na primeira vez, baixa os dados do CNEFE (~1 GB) para o cache do usuário. Depois roda sem internet.
- Só grava pontos no número ou na rua certa, dentro do município; coordenada oficial tem sempre prioridade.
- `python -m src.pipeline --apenas geocodificacao`

Detalhes em `docs/decisoes/DEC-002-geocodificacao-das-escolas.md`.

### Download do INEP

O servidor `download.inep.gov.br` não envia o certificado intermediário da sua cadeia TLS, então downloads comuns falham com `unable to get local issuer certificate`. O projeto inclui esse intermediário em `backend/certs/` e o soma às autoridades padrão (certifi) só para o INEP. A verificação de segurança **nunca** é desligada.

- Certificado: RNP ICPEdu GR46 OV TLS CA 2025, emitido por GlobalSign Root R46.
- Validade: até 19/11/2030.
- SHA-256: `E1:07:47:D4:DA:7B:AB:09:CB:A9:95:2F:01:9D:35:34:CB:9F:BA:07:0B:F1:3D:87:91:B1:69:9C:D2:FF:59:DD`

## API

A API lê as views do banco e entrega JSON para o frontend. Ela **não grava nada**: cada requisição roda numa transação `READ ONLY`, com tempo limite de 10 segundos.

```bash
cd backend
uvicorn api.main:app --reload
```

- Documentação interativa: http://127.0.0.1:8000/docs (dá para testar cada endereço clicando em "Try it out").
- O frontend em `http://localhost:5173` (Vite) ou `http://localhost:3000` já é aceito. Para outros endereços, use `VELTIS_CORS_ORIGENS` no `.env`.

| Endereço | O que devolve |
| --- | --- |
| **`GET /mapa/instituicoes`** | **Escolas e faculdades numa lista só, com `latitude` e `longitude`, no formato do frontend.** Filtros: `municipio`, `tipo` (`escola`, `etec`, `fatec`, `faculdade`), `busca` |
| `GET /municipios` | GeoJSON com o contorno dos 27 municípios (`?detalhe=completo` para o contorno original) |
| `GET /municipios/indicadores` | Indicadores do IBGE de todos os municípios |
| `GET /municipios/{cd_mun}` | Ficha do município: indicadores + resumo da educação |
| `GET /escolas` | GeoJSON com as escolas que têm coordenada. Filtros: `municipio`, `dependencia`, `apenas_ativas`, `ensino_medio`, `educacao_profissional`, `busca` |
| `GET /escolas/sem-localizacao` | Escolas sem coordenada (lista paginada) |
| `GET /escolas/{co_entidade}` | Ficha da escola com os cursos técnicos |
| `GET /cursos-tecnicos` | Cursos técnicos. Filtros: `municipio`, `area`, `escola`, `incluir_magisterio`, `busca` |
| `GET /cursos-superiores` | Graduação por município de oferta. Filtros: `municipio`, `ies`, `modalidade`, `grau`, `area`, `rede`, `gratuito`, `apenas_com_matricula`, `busca` |
| `GET /instituicoes` | Faculdades por município, com a contagem de cursos presenciais e EAD e os campi com coordenada (`locais`) |
| `GET /filtros` | Opções prontas para os campos de seleção do site |
| `GET /fontes` | Última carga de cada arquivo oficial |
| `GET /saude` | Confirma que a API e o banco estão respondendo |

Regras comuns:

- Listas são paginadas: `?pagina=1&por_pagina=50` (máximo 500). A resposta traz `total`, `pagina`, `por_pagina` e `itens`.
- Sem `ano`, cada endereço usa a edição mais recente carregada.
- A `busca` ignora maiúsculas e acentos (`sao roque` acha "São Roque").
- Filtro inválido responde `422`, item inexistente `404` e banco fora do ar `503`.

## Views para a API

| View | Conteúdo |
| --- | --- |
| `vw_municipios_mapa` | Contorno dos 27 municípios (EPSG:4326) + população 2022 |
| `vw_indicadores_municipio` | Uma linha por município: população, sexo, faixas de idade, alfabetização, frequência escolar, instrução |
| `vw_escolas_mapa` | Uma linha por escola, com a melhor localização disponível, rótulos em texto e coordenadas em EPSG:4326 |
| `vw_cursos_tecnicos` | Cursos de educação profissional por escola |
| `vw_cursos_superiores` | Ofertas de graduação por município de oferta, com a IES |
| `vw_faculdades_mapa` | Um ponto por campus presencial, com a faculdade e os cursos (EPSG:4326) |
| `vw_faculdades_sem_local` | Ofertas presenciais ainda sem campus com coordenada (deve ficar vazia) |
| `vw_ultimas_cargas` | Auditoria: última carga de cada arquivo |

## Testes

```bash
pytest                    # testes unitários (sem banco e sem internet)
```

Testes da API no banco do `.env`. Como a API só lê, é seguro rodar até no Supabase:

```bash
VELTIS_TESTE_API=1 pytest tests/test_api.py          # Linux/Mac
set VELTIS_TESTE_API=1 && pytest tests/test_api.py   # Windows (cmd)
```

Os testes de integração precisam de um banco PostgreSQL + PostGIS **vazio e descartável** (nunca o Supabase):

```bash
VELTIS_TESTE_DATABASE_URL=postgresql+psycopg://postgres:senha@localhost:5432/veltis_teste pytest
```

## Regras de dados

- O Censo Escolar define o universo de escolas. Catálogo e SEDUC só enriquecem.
- Coordenada ausente fica `NULL`. Nada é inventado, e coordenada oficial é diferente de geocodificada.
- O município do curso superior é o **local de oferta**, não a sede da IES.
- Escola sem coordenada oficial pode ganhar ponto **geocodificado** (IBGE CNEFE), sempre marcado com a precisão; nunca centro de CEP, bairro ou município.
- O INEP não publica coordenadas das faculdades. O ponto de cada campus está em `backend/data/referencia/ies_locais_oferta.csv`, com a fonte do endereço e a precisão (`edificio`, `numero` ou `rua`). Ver `docs/decisoes/DEC-001-coordenadas-das-faculdades.md`.
- No SIDRA, as categorias são pedidas explicitamente: `[all]` mistura níveis e conta em dobro.
- Taxas não se somam entre municípios.

