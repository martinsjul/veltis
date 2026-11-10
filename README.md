# Veltis

Portal web com mapa das escolas, faculdades, cursos e indicadores demográficos dos 27 municípios da Região Metropolitana de Sorocaba (RMS), a partir de dados públicos oficiais.

> O histórico de evolução do projeto está na seção [Atualizações](#atualizações).

## Identificação

- **Projeto:** Veltis
- **Equipe:** Julia Ribeiro Martins (backend e dados) e Daniel Lansana de Almeida (frontend)
- **Orientação:** prof. Munari
- **Cliente ou parceiro:** não há cliente externo; público-alvo: estudantes e pesquisadores, órgãos públicos, instituições de ensino e cidadãos interessados em dados da RMS
- **Disciplina/etapa:** Projeto Integrador — ADS, Fatec Sorocaba, 2º semestre de 2026 (continuação do 1º semestre de 2026)
- **Versão analisada:** branch `main`
- **Atualizado em:** 2026-11-03

## Resumo do projeto

Quem quer saber quais escolas e faculdades existem na sua cidade, que cursos elas oferecem e como o município se compara aos vizinhos precisa consultar vários sites do IBGE, do INEP e da Secretaria da Educação, com formatos e códigos diferentes. O Veltis reúne esses dados num só lugar e mostra tudo num mapa.

**Produzido até agora:** banco PostgreSQL/PostGIS com os dados oficiais dos 27 municípios (malha do IBGE, indicadores do Censo 2022, 1.806 escolas do Censo Escolar 2025, 435 cursos técnicos, 115 instituições de ensino superior e 10.381 ofertas de cursos do Censo Superior 2024); sete pipelines que baixam, validam e carregam esses dados; e uma API de leitura com 13 endereços, que entrega escolas e faculdades com latitude e longitude. A primeira versão do portal (React + MapTiler) está em desenvolvimento.

**Ainda não validado:** o portal ligado à API real e a avaliação com usuários.

## Problema, objetivos e avaliação

- **Problema:** os dados educacionais e demográficos da RMS são públicos, mas estão espalhados em várias fontes, em arquivos grandes e com códigos, e as instituições de ensino superior não têm coordenadas publicadas.
- **Objetivo:** construir um portal web gratuito que mostre no mapa as escolas e faculdades da RMS, seus cursos e os indicadores de cada município, com dados oficiais e rastreáveis.
- **Como será avaliado:** testes automáticos do backend; verificação de qualidade do banco após cada carga; comparação dos dados exibidos com as fontes oficiais; demonstração do portal e avaliação com usuários (ver [`docs/testes/`](docs/testes/plano-e-evidencias-de-testes.md)).

## Escopo e situação desta versão

### Incluído ou produzido

| Item | Estado |
| --- | --- |
| Banco PostgreSQL/PostGIS com migrations versionadas (001 a 005) | Concluído |
| Pipelines: malha IBGE, SIDRA, Censo Escolar, localização das escolas, geocodificação, Censo Superior, locais das faculdades | Concluído (carga no Supabase em 2026-11-06) |
| API de leitura (FastAPI) com GeoJSON, filtros, busca e paginação | Concluído |
| Coordenadas das 33 faculdades com curso presencial (39 campi) | Concluído |
| Portal web: mapa, filtros, painel da instituição | Em andamento (branch `front-end`) |
| Documentação no modelo do professor | Concluído (2026-11-03) |

### Fora do escopo ou ainda não iniciado

- Dashboards no Power BI e Data Warehouse em esquema estrela: trabalho futuro ([DEC-007](docs/decisoes/DEC-007-power-bi-e-data-warehouse.md)).
- IDH: não está disponível nas fontes usadas (o Censo 2022 não publica IDH).
- Aplicativo móvel.

### Limitações, premissas e riscos

- **Escolas sem coordenada:** 227 das 1.806 escolas não têm coordenada oficial. A geocodificação pelo endereço deu ponto a 43 delas em 2026-11-06 ([DEC-002](docs/decisoes/DEC-002-geocodificacao-das-escolas.md)); hoje 1.622 escolas aparecem no mapa e as 184 restantes (154 em atividade) aparecem numa lista à parte, porque o endereço delas só permitiu achar o CEP, o bairro ou o município.
- **Faculdades:** o INEP não publica coordenadas; os pontos dos campi foram levantados pela equipe e 3 deles estão só na rua certa ([DEC-001](docs/decisoes/DEC-001-coordenadas-das-faculdades.md)).
- **Arquivos manuais:** Catálogo de Escolas do INEP e SEDUC-SP não têm download automático.
- **Edições:** Censo Escolar 2025 e Censo Superior 2024; o Censo Superior 2025 sai depois do fim do semestre.

## Organização do código

O projeto usa **componentes separados**:

| Pasta/arquivo | Propósito |
| --- | --- |
| [`backend/`](backend/README.md) | Banco (migrations), pipelines de dados (`src/`) e API (`api/`). Guia técnico completo no README da pasta. |
| [`frontend/`](frontend/README.md) | Portal web em React + Vite + MapTiler. O código atual está na branch `front-end`. |
| [`docs/`](docs/README.md) | Documentação: requisitos, casos de uso, dados (DER e dicionário), arquitetura, testes, decisões e continuidade. |
| [`PRODUCT-BACKLOG.md`](PRODUCT-BACKLOG.md) | Itens de trabalho priorizados e pendências. |

Os pipelines de dados ficam dentro de `backend/src/`, e não numa pasta `data/` separada, porque usam a mesma conexão e as mesmas validações do backend. As fontes e a proveniência estão em [`docs/dados/README.md`](docs/dados/README.md).

## Componentes e evidências

| Componente ou frente | Estado | Evidência e localização |
| --- | --- | --- |
| Banco de dados | concluído | `backend/database/migrations/`; verificação de 2026-10-19 sem erros |
| Pipelines de dados | concluído | `backend/src/`; `docs/testes/` §4.2 |
| API | concluído | `backend/api/`; 30 testes da API; teste manual em 2026-10-26 |
| Portal web | em andamento | branch `front-end`; `frontend/README.md` |
| Aplicativo móvel | N/A | — |
| Requisitos, casos de uso e modelos | concluído (revisão 2026-11-03) | `docs/requisitos/`, `docs/caso_de_uso/`, `docs/dados/`, `docs/arquitetura/` |
| Testes e validação | em andamento | `docs/testes/` |
| Documento acadêmico | em andamento | mantido pela equipe fora do repositório |

## Rastreabilidade do projeto

| Necessidade/objetivo | Requisito | Caso de uso | Implementação | Validação | Estado |
| --- | --- | --- | --- | --- | --- |
| Ver as instituições no mapa | RF-01, RF-04 | UC-01, UC-04 | `/municipios`, `/mapa/instituicoes`; views `vw_escolas_mapa`, `vw_faculdades_mapa` | CT-14 | API concluída; interface em andamento |
| Encontrar uma instituição | RF-02, RF-03 | UC-02, UC-07 | filtros `municipio`, `tipo`, `dependencia`, `rede`, `busca` | CT-11, CT-15 | API concluída |
| Saber o que cada instituição oferece | RF-05 | UC-05, UC-06 | `/escolas/{codigo}`, `/cursos-tecnicos`, `/cursos-superiores` | testes da API | API concluída; interface a validar |
| Comparar municípios | RF-06 | UC-03 | `/municipios/{codigo}`, `vw_indicadores_municipio` | testes da API | API concluída; interface planejada |
| Confiar nos dados | RF-07, RF-08, RNF-06, RNF-08 | UC-08 | pipelines, `controle_ingestao`, `/fontes` | verificação do banco | concluído |

## Continuidade entre semestres

O projeto começou no 1º semestre de 2026 com a estrutura de pastas e o README de apresentação (arquivos de código vazios, commit `5aa840d`). Tudo o que funciona hoje foi feito no 2º semestre de 2026. Detalhes em [`docs/continuidade/`](docs/continuidade/README.md).

## Como começar

1. Leia [`docs/README.md`](docs/README.md) para encontrar cada documento.
2. Backend: siga [`backend/README.md`](backend/README.md) (Python, `.env`, migrations, pipelines, API).
3. Frontend: siga `frontend/README.md` (Node.js, `VITE_API_URL`, `VITE_MAPTILER_KEY`).
4. Nunca versione senhas, tokens ou o arquivo `.env`.

## Atualizações

### 2026-11-10

- **Backend Java/Spring Boot (branch `backend-java`)** Julia: projeto em `backend-java/` para a disciplina Técnicas Avançadas de Programação — Spring Data JPA, H2 com dados reais da RMS, CRUD, DTOs/Mappers, Bean Validation e relacionamentos JPA (Município 1:N Escola, Escola 1:1 Localização, Escola N:N Curso técnico, Instituição 1:N Campus e Curso). Ver `backend-java/README.md`.
- **Requisitos resumidos** Julia: a pedido do orientador, os requisitos funcionais de consulta foram agrupados (de 14 para 8, especificação 0.4) e os casos de uso de 12 para 8 (versão 1.2); README, backlog e plano de testes atualizados com a nova numeração.
- **Otimização do Front e Pins das Instituições de Superior** Daniel: mapa consegue exibir todas as instituições, informações das instituições carregam mais rápido, e os filtros funcionam corretamente por rede, cidade e/ou nome.

### 2026-11-06

- **Latitude e longitude no Supabase** Julia: migrations 004 e 005 aplicadas; 39 campi das faculdades carregados; geocodificação deu ponto a 43 das 198 escolas sem coordenada oficial que tinham endereço (21 no número, 8 em número vizinho, 14 na rua). `/mapa/instituicoes` passa a entregar 1.622 escolas e 39 campi com latitude e longitude. Código da API e dos pipelines enviado ao repositório.

### 2026-11-03

- **Coordenadas das faculdades e geocodificação das escolas** Julia: tabela `ies_local_oferta` com os 39 campi presenciais (endereço oficial + OpenStreetMap/CNEFE), pipeline `geocodificacao` (geocodebr/IBGE CNEFE) para as escolas sem coordenada oficial, migrations 004 e 005, endereço `/mapa/instituicoes` na API (escolas e faculdades com latitude e longitude) e registros DEC-001 e DEC-002 em `docs/decisoes/`.
- **Documentação no padrão do repositório-modelo** Julia (revisando o material do Daniel): README no formato do template, guia técnico em `backend/README.md`, requisitos e casos de uso alinhados, arquitetura, testes, decisões DEC-003 a DEC-007, continuidade, backlog, dicionário de dados atualizado.
- **Organização da documentação** Daniel: reorganização dos documentos do projeto na pasta `docs/`.
- **Adicionando registro de atualizações** Daniel: antigos commits registrados na seção de atualizações.

### 2026-10-26

- **API de leitura + guia da API para o frontend** Julia: guia que explica ao frontend como consumir a API.
- **API FastAPI de leitura, com 12 endereços** Julia: primeira versão da API sobre as views do banco.

### 2026-10-19

- **Backend completo: migrations, pipelines, views e localização das escolas** Julia: migrations 001 a 003, os 5 coletores, as views de leitura e o enriquecimento da localização das escolas (INEP + SEDUC-SP).

### 2026-09-28

- **Documentos antigos removidos** Julia: exclusão de `Veltis_Metadados.docx`, `Veltis_Dicionario_de_Dados.xlsx` e `Veltis_Bases_e_Fontes_de_Dados.docx` de `docs/`.
- **Arquivos adicionados por upload** Daniel: novos arquivos de documentação enviados ao repositório.

### 2026-09-27

- **Organiza estrutura atual do Veltis e remove arquivos antigos** Julia: limpeza do repositório e ajuste da estrutura de pastas.
- **Estrutura inicial e pipelines de dados do Veltis** Julia: primeira estrutura dos pipelines de coleta.

### 2026-09-21

- **Adicionando documentação dos dados** Daniel: dicionário de dados, metadados e fontes.

### 2026-09-17

- **Banco PostGIS e importação inicial dos dados IBGE** Julia: criação do banco PostgreSQL/PostGIS e primeira carga do IBGE.

### 2026-08-03

- **Scripts de importação de dados IBGE, INEP e MEC** Julia: primeiros scripts de importação das três fontes.

### 2026-06-09

- **Alterando README** Julia.
- **Adicionando estrutura base do Frontend** Julia: criação da pasta `frontend/`.
- **Estrutura inicial do projeto Veltis** Julia: organização inicial das pastas.
- **Initial commit** Julia: criação do repositório.
