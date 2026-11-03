# Linha de base e evolução — 2º semestre de 2026

- **Projeto:** Veltis
- **Equipe atual:** Julia Ribeiro Martins (backend e dados) e Daniel Lansana de Almeida (frontend)
- **Orientador:** prof. Munari
- **Período:** 2º semestre de 2026
- **Origem do trabalho anterior:** este mesmo repositório (`martinsjul/veltis`), 1º semestre de 2026
- **Versão recebida no início:** commit `5aa840d` (2026-06-09), último do 1º semestre
- **Como o estado inicial foi conferido:** leitura dos arquivos no commit `5aa840d` (`git ls-tree -r -l 5aa840d`)
- **Limitações da comparação:** não há registro de testes ou demonstrações do 1º semestre além do repositório. Um terceiro integrante citado em documentos anteriores deixou o grupo e não tem commits no repositório.

## Estado recebido no início do semestre

No commit `5aa840d` o repositório tinha a **estrutura de pastas e o README de apresentação**. Todos os arquivos de código e de documentação estavam vazios (0 bytes).

| Item | Estado inicial | Evidência da linha de base | Limitação conhecida |
| --- | --- | --- | --- |
| README de apresentação (objetivo, público-alvo, funcionalidades pretendidas) | planejado | `README.md` em `5aa840d` (920 bytes) | Descreve intenção, não funcionalidade pronta |
| Estrutura de pastas do backend (`app/`, `scripts/`) e do frontend (`src/components`, `pages`, `services`) | estrutura vazia | arquivos com 0 bytes em `5aa840d` | Sem código |
| Documentação (`docs/api.md`, `arquitetura.md`, `banco-de-dados.md`) | estrutura vazia | arquivos com 0 bytes em `5aa840d` | Sem conteúdo |
| Banco de dados, pipelines, API e telas | não iniciado | ausentes | — |

## O que mudou neste semestre

| Item | Classificação | Situação inicial → atual | Trabalho desenvolvido | Evidência | Validação |
| --- | --- | --- | --- | --- | --- |
| Banco PostgreSQL/PostGIS | novo | não existia → implementado | Modelo com 10 tabelas (mais o registro das migrations), chaves, índices espaciais, RLS e 5 migrations versionadas | `backend/database/migrations/`; commits `44ef6e6`, `8d78d02` | Migrations aplicadas no Supabase; teste de integração `tests/test_banco.py` |
| Pipelines de dados (7 etapas) | novo | não existia → implementado | Malha IBGE, SIDRA, Censo Escolar, localização das escolas, geocodificação, Censo Superior, locais das faculdades; controle de cargas com hash e status | `backend/src/`; commits `2bb780e`, `b51b44c`, `8d78d02` | `python -m src.pipeline --verificar` sem erros em 2026-10-19 (ver `docs/testes/`) |
| Views de leitura | novo | não existia → implementado | 8 views com códigos traduzidos e coordenadas em WGS 84 | migrations 003 a 005 | Testes da API |
| API FastAPI | novo | não existia → implementado | 13 endereços de leitura, GeoJSON e lista para o mapa, paginação, filtros | `backend/api/`; commits `fa80c70`, `f7c2656` | Testes automáticos; teste manual em 2026-10-26 contra o Supabase |
| Coordenadas das faculdades | novo | não existia → implementado | 39 campi presenciais com latitude/longitude | `backend/data/referencia/`; DEC-001 | Todos os pontos dentro do município correto |
| Geocodificação das escolas sem ponto | novo | não existia → implementado | Etapa automática com geocodebr/IBGE CNEFE | DEC-002 | Teste local; execução no Supabase pendente |
| Frontend React | herdado e alterado | estrutura vazia → em desenvolvimento | Primeira versão com mapa (MapTiler), filtros e painel da instituição | branch `front-end`, commit `3b29fe5` | A validar com a API real |
| Documentação no modelo do professor | herdado e alterado | arquivos vazios → em andamento | Requisitos, casos de uso, DER, dicionário de dados, decisões, testes, continuidade | `docs/`; commits `8b3a3a3`, `7985bbe`, `a801816` | Revisão da equipe |
| Power BI e Data Warehouse | pendente | planejado → planejado | Nenhum (trabalho futuro) | DEC-007; `PRODUCT-BACKLOG.md` | — |

## Contribuições dos integrantes

| Integrante | Atividade | Artefatos | Evidência | Observação |
| --- | --- | --- | --- | --- |
| Julia Ribeiro Martins | Modelagem do banco, pipelines de dados, views, API, documentação técnica | `backend/`, `docs/decisoes/`, `docs/dados/` | commits `2bb780e`, `44ef6e6`, `b51b44c`, `8d78d02`, `fa80c70`, `f7c2656` | Responsável pelo backend |
| Daniel Lansana de Almeida | Frontend (React, MapTiler), documentação de dados, requisitos, casos de uso e DER | branch `front-end`, `docs/caso_de_uso/`, `docs/requisitos/`, `docs/dados/der-veltis-03-11.md` | commits `8b3a3a3`, `3b29fe5`, `d787ce4`, `7985bbe`, `a801816` | Responsável pelo frontend |

O detalhamento está em [`contribuicoes.csv`](contribuicoes.csv).

## Decisões e próximos passos

- **Decisões do semestre:** DEC-001 a DEC-007 em `docs/decisoes/`.
- **Pendências:** levar o frontend da branch `front-end` para a `main` e ligá-lo à API real; rodar a geocodificação no Supabase; validar o portal com usuários; protótipos de tela em `docs/prototipos/`; documento acadêmico.
- **Próximos passos:** ver [`PRODUCT-BACKLOG.md`](../../PRODUCT-BACKLOG.md).
