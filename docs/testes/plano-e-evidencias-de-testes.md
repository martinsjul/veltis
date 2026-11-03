# Plano e evidências de testes — Veltis

- **Versão:** 1.0
- **Atualizado em:** 2026-11-03
- **Escopo:** banco de dados, pipelines de dados e API (backend). Os testes do frontend ficam a cargo da equipe de frontend e serão registrados aqui quando realizados.

## 1. Estratégia

| Nível | O que verifica | Ferramenta | Onde |
| --- | --- | --- | --- |
| Unitário | Transformações (códigos, valores do SIDRA, endereços), validações, regras de seleção de pontos, montagem de GeoJSON e filtros da API | `pytest` | `backend/tests/` (rodam sem banco e sem internet) |
| Integração com o banco | Migrations aplicadas do zero, unicidade das chaves, RLS ligado | `pytest` + PostgreSQL/PostGIS descartável | `backend/tests/test_banco.py` |
| Integração da API | Cada endereço contra um banco com dados (a API só lê, então pode rodar contra o Supabase) | `pytest` + FastAPI TestClient | `backend/tests/test_api.py` |
| Qualidade dos dados | Contagens e regras de consistência depois de cada carga | `python -m src.pipeline --verificar` | `backend/src/verificar.py` |
| Manual | Endereços da API pela página `/docs` | navegador | — |

## 2. Ambiente

- Python 3.13, PostgreSQL 17.6 + PostGIS 3.3 (Supabase) e PostgreSQL 16 + PostGIS local para os testes de integração.
- Dados de teste: os testes unitários usam dados fictícios montados no próprio teste. Os testes de integração com o banco usam um banco **vazio e descartável** (variável `VELTIS_TESTE_DATABASE_URL`), nunca o Supabase.

Como rodar (dentro de `backend/`):

```bash
pytest                                              # unitários
VELTIS_TESTE_DATABASE_URL=postgresql+psycopg://... pytest tests/test_banco.py
VELTIS_TESTE_API=1 pytest tests/test_api.py         # API contra o banco do .env
```

## 3. Casos de teste principais

| ID | Requisito / regra | Cenário | Resultado esperado | Arquivo |
| --- | --- | --- | --- | --- |
| CT-01 | RN-06 | Valor do SIDRA com símbolo especial ("-", "X", "..") | Vira 0 ou nulo conforme a regra, e o símbolo original é guardado | `test_transforms.py` |
| CT-02 | RN-06 | Mesmo indicador com classificações diferentes | Chaves de classificação diferentes; nada é contado em dobro | `test_transforms.py`, `test_banco.py` |
| CT-03 | RN-08 | Arquivo nacional do Censo Escolar | Só as escolas dos 27 municípios da RMS são mantidas | `test_coletores.py` |
| CT-04 | RN-09 | Curso superior nas dimensões 1 a 4 | Só as dimensões 1 e 2 dentro da RMS são carregadas | `test_coletores.py` |
| CT-05 | RN-03, RN-07 | Coordenada inválida ou fora de SP na localização das escolas | Coordenada descartada; escola continua cadastrada | `test_coletores.py` |
| CT-06 | RN-07 | Endereço da escola nos formatos do Catálogo INEP e da SEDUC-SP | Logradouro, número, bairro e CEP separados corretamente | `test_geocodificacao.py` |
| CT-07 | RN-07 | Resultado da geocodificação com precisão de CEP, bairro ou margem grande | Ponto recusado; só número ou rua com margem pequena entram | `test_geocodificacao.py` |
| CT-08 | RN-03 | Arquivo de locais das faculdades com latitude/longitude trocadas, município fora da RMS, precisão inválida ou duplicidade | Carga recusada com mensagem clara | `test_locais_ies.py` |
| CT-09 | RNF-08 | Banco criado do zero | Todas as migrations aplicadas; tabela de classificações removida; RLS ligado em todas as tabelas | `test_banco.py` |
| CT-10 | RNF-08 | Duas cargas do mesmo valor, fonte ou oferta | O banco recusa a duplicidade (chave única) | `test_banco.py` |
| CT-11 | RNF-07 | Filtro com valor inválido na API (`dependencia=particular`, `municipio=abc`, `por_pagina=1000`) | HTTP 422, sem consultar o banco | `test_api.py` |
| CT-12 | RNF-07 | Banco fora do ar | HTTP 503 com mensagem simples, sem expor senha ou detalhe técnico | `test_api.py` |
| CT-13 | RNF-07 | Tentativa de escrita pela conexão da API | Recusada (transação somente leitura) | `test_api.py` |
| CT-14 | RF-07 | `/mapa/instituicoes` | Todos os itens com latitude e longitude; tipos Escola, ETEC, FATEC e Faculdade/Universidade | `test_api.py` |
| CT-15 | RF-06 | Termo de busca "  São ROQUE " | Vira o padrão `%sao roque%` (ignora acentos e maiúsculas; curingas escapados) | `test_api.py` |

## 4. Resultados observados

### 4.1 Testes automáticos

| Data | Ambiente | Resultado |
| --- | --- | --- |
| 2026-11-03 | Local, Python 3.13 | **80 testes unitários passaram**; 15 de integração pulados por falta de banco (comportamento esperado) |
| 2026-11-03 | PostgreSQL 16 + PostGIS local, banco vazio | `test_banco.py`: **6 passaram** (migrations 001 a 005 do zero) |
| 2026-11-03 | PostgreSQL local com cópia dos dados do INEP/IBGE | `test_api.py`: **30 passaram** |

### 4.2 Verificação da carga no Supabase (2026-10-19)

Resultado de `python -m src.pipeline --verificar`: **sem erros**.

| Verificação | Resultado |
| --- | --- |
| Municípios da RMS | 27 |
| Valores demográficos (7 tabelas do SIDRA) | 2.376 |
| Escolas (Censo Escolar 2025) / em atividade | 1.806 / 1.672 |
| Cursos técnicos | 435 |
| Escolas com localização em alguma fonte | 1.777 |
| Escolas com ponto no mapa (coordenada oficial) | 1.579 |
| Escolas sem coordenada oficial | 227 |
| Pontos oficiais fora do polígono do município | 5 (sinalizados, não removidos) |
| Instituições de ensino superior com oferta na RMS / com curso presencial | 115 / 33 |
| Ofertas de cursos superiores / presenciais | 10.381 / 375 |

### 4.3 Teste manual da API (2026-10-26)

API executada num computador da Fatec, ligada ao Supabase pelo *Session pooler*. Endereço `/saude` respondeu `{"status": "ok", "banco": "ok"}` depois de corrigido o usuário da conexão (o primeiro teste falhou com `password authentication failed`, o que confirmou a mensagem de erro esperada sem expor a senha).

### 4.4 Locais das faculdades e geocodificação (2026-11-03, banco local)

- 39 locais de faculdades carregados; todos dentro do polígono do município; 0 ofertas presenciais sem local.
- Geocodificação: em 12 endereços de teste, 10 receberam ponto (7 no número exato, 2 em número vizinho, 1 na rua) e 2 foram recusados corretamente (um endereço inexistente e um sem CEP que só casou com o município).
- **Pendente:** executar as etapas `geocodificacao` e `locais_ies` no Supabase e registrar aqui quantas das 227 escolas ganharam ponto.

## 5. Avaliação com usuários

Ainda não realizada. Será registrada aqui (roteiro, participantes anonimizados, tarefas e resultados) quando o frontend estiver ligado à API.
