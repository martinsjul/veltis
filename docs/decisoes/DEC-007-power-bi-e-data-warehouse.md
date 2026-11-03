# DEC-007 — Power BI e Data Warehouse como trabalho futuro

- **Estado:** aceita
- **Data:** 2026-11-03
- **Responsáveis pela decisão:** equipe do projeto
- **Relacionado a:** escopo do projeto; `PRODUCT-BACKLOG.md`

## Contexto

A proposta inicial do Veltis previa, além do portal com mapa, uma área de dashboards analíticos no Power BI ligada a um Data Warehouse em esquema estrela no PostgreSQL, voltada a pesquisadores e gestores públicos. Neste semestre, a equipe priorizou a base de dados, os pipelines, a API e o portal.

## Alternativas consideradas

- **Fazer agora:** dividiria o esforço antes de o portal estar completo.
- **Registrar como trabalho futuro:** mantém a ideia documentada sem prometer o que não foi feito.

## Decisão e justificativa

Power BI e Data Warehouse ficam **fora do escopo desta versão** e entram no backlog como trabalho futuro. Nenhum documento do projeto deve apresentá-los como implementados.

## Consequências e revisão

- O banco atual já tem dados limpos, rastreáveis e com chaves estáveis, o que facilita montar um esquema estrela depois (fatos: ofertas de cursos, escolas, indicadores; dimensões: município, tempo, instituição).
- Revisar no planejamento do próximo semestre.
