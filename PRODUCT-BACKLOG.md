# Product Backlog — Veltis

- **Produto:** portal web com mapa das escolas, faculdades, cursos e indicadores da Região Metropolitana de Sorocaba
- **Objetivo do produto:** reunir num só lugar, com dados oficiais, a oferta educacional e os indicadores dos 27 municípios da RMS
- **Atualizado em:** 2026-11-03

Prioridade: Alta / Média / Baixa. Estado: Pronto / Em andamento / A fazer / Futuro.

| ID | Item | Requisito | Prioridade | Responsável | Estado |
| --- | --- | --- | --- | --- | --- |
| PB-01 | Banco PostGIS com migrations versionadas | RNF-08 | Alta | Julia | Pronto |
| PB-02 | Pipelines das fontes oficiais com controle de cargas | RF-08 | Alta | Julia | Pronto |
| PB-03 | API de leitura com GeoJSON, filtros e paginação | RF-01 a RF-07 | Alta | Julia | Pronto |
| PB-04 | Coordenadas dos campi das faculdades | RF-04 | Alta | Julia | Concluído (Supabase, 2026-11-06) |
| PB-05 | Geocodificação das escolas sem coordenada | RF-04 | Média | Julia | Concluído (Supabase, 2026-11-06: 43 escolas ganharam ponto) |
| PB-06 | Levar o frontend da branch `front-end` para a `main` | RF-01, RF-04 | Alta | Daniel | Concluído (2026-11-10, commit `352baab`) |
| PB-07 | Ligar o frontend à API real (`/mapa/instituicoes`) | RNF-04 | Alta | Daniel | Em andamento |
| PB-08 | Painel de detalhes da escola e da faculdade, com cursos | RF-05 | Alta | Daniel | Em andamento |
| PB-09 | Ficha do município com indicadores | RF-06 | Média | Daniel | A fazer |
| PB-10 | Lista "Escolas sem localização" | RF-04 | Média | Daniel | A fazer |
| PB-11 | Rodapé com fontes, data de atualização e atribuições | RF-07, RNF-10 | Média | Daniel | A fazer |
| PB-12 | Controle de camadas do mapa | RF-01 | Baixa | Daniel | A fazer |
| PB-13 | Protótipos de tela em `docs/prototipos/` | RNF-01 | Média | Daniel | A fazer |
| PB-14 | Avaliação com usuários e registro em `docs/testes/` | RNF-01 | Média | Equipe | A fazer |
| PB-15 | Documento acadêmico (mantido pela equipe fora do repositório): fundamentação, resultados e considerações finais | — | Alta | Equipe | Em andamento |
| PB-16 | Publicar a API e o portal num endereço público | RNF-04 | Média | Equipe | A fazer |
| PB-17 | Atualizar para o Censo da Educação Superior 2025 quando for publicado | RF-08 | Baixa | Julia | Futuro |
| PB-18 | Data Warehouse em esquema estrela no PostgreSQL | — | Baixa | Equipe | Futuro (DEC-007) |
| PB-19 | Dashboards analíticos no Power BI | — | Baixa | Equipe | Futuro (DEC-007) |
