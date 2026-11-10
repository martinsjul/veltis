# Documentação do Veltis

Registros que explicam requisitos, modelos, decisões, testes e continuidade do projeto, organizados conforme o repositório-modelo do Projeto Integrador (ADS/AMS Fatec).

## Onde está cada coisa

| Pasta | Para que serve | Arquivos |
| --- | --- | --- |
| [`requisitos/`](requisitos/especificacao-requisitos-veltis-03-11.md) | Requisitos funcionais e não funcionais, regras de negócio e critérios de aceite | `especificacao-requisitos-veltis-03-11.md` |
| [`caso_de_uso/`](caso_de_uso/casos-de-uso-veltis-03-11.md) | Diagrama e especificação dos 12 casos de uso | `casos-de-uso-veltis-03-11.md` |
| [`dados/`](dados/README.md) | Fontes e proveniência, DER e dicionário de dados | `README.md`, `der-veltis-03-11.md`, `Veltis_Dicionario_de_Dados_Completo_2026-11-03.xlsx` |
| [`arquitetura/`](arquitetura/README.md) | Visão arquitetural e diagrama de classes | `visao-arquitetural.md`, `diagrama-de-classes.md` |
| [`testes/`](testes/plano-e-evidencias-de-testes.md) | Plano de testes e resultados observados | `plano-e-evidencias-de-testes.md` |
| [`decisoes/`](decisoes/README.md) | Decisões de escopo, dados e arquitetura (DEC-001 a DEC-007) | `DEC-*.md` |
| [`continuidade/`](continuidade/README.md) | Linha de base do 1º semestre e evolução do 2º semestre de 2026; contribuições | `linha-de-base-e-evolucao-2026-2.md`, `contribuicoes.csv` |
| `uso interno/` | Guias para a equipe: como ligar a API e como o frontend consome a API | `PASSO_A_PASSO_LIGAR_A_API.md`, `GUIA_API_PARA_O_FRONTEND.md` |

O backlog do produto fica na raiz do repositório: [`PRODUCT-BACKLOG.md`](../PRODUCT-BACKLOG.md).

Protótipos de tela (`prototipos/`) ainda não foram registrados; serão acrescentados pela equipe de frontend.

## Relação entre os documentos

Requisitos (RF/RNF/RN) → casos de uso (UC) → implementação (`backend/`, `frontend/`) → testes (CT). A tabela de rastreabilidade está no [README principal](../README.md#rastreabilidade-do-projeto).
