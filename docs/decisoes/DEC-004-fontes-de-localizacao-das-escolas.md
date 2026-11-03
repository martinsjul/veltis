# DEC-004 — Universo e localização das escolas

- **Estado:** aceita
- **Data:** 2026-10-19
- **Responsáveis pela decisão:** equipe do projeto
- **Relacionado a:** pipelines `censo_escolar` e `localizacao`; tabela `ESCOLA_LOCALIZACAO`; `vw_escolas_mapa`; DEC-002

## Contexto

Os microdados do Censo Escolar trazem todas as escolas, mas **não trazem endereço nem coordenadas**. O Catálogo de Escolas do INEP e a base Escolas Ativas da SEDUC-SP trazem endereço e, na maioria dos casos, latitude e longitude. As três fontes não têm exatamente as mesmas escolas.

## Alternativas consideradas

- **Usar o Catálogo como lista de escolas:** tem coordenadas, mas inclui registros fora do Censo e não traz os indicadores de oferta (ensino médio, técnico).
- **Usar o Censo Escolar como universo e as outras fontes só para localizar:** a lista de escolas é a oficial do Censo; endereço e ponto entram como informação complementar, com a fonte registrada.

## Decisão e justificativa

O **Censo Escolar define quais escolas existem** (`INEP_ESCOLA`). Catálogo INEP e SEDUC-SP só **complementam** endereço e coordenada em `ESCOLA_LOCALIZACAO`, uma linha por escola e fonte. Código fora do Censo ou fora da RMS é ignorado. Na view do mapa, a coordenada oficial do Catálogo tem prioridade; depois a da SEDUC; e só então o ponto geocodificado (DEC-002). Coordenada ausente fica nula: nada é inventado.

## Consequências e revisão

- Validação de 19/10/2026: 1.806 escolas no Censo (RMS), 1.777 com localização em alguma fonte e 1.579 com ponto oficial; 227 sem coordenada oficial e 5 pontos fora do polígono do município (sinalizados em `ponto_confere_municipio`).
- O Catálogo e a SEDUC não têm download automático: os arquivos são exportados à mão e colocados em `backend/data/raw`.
- Revisar a cada nova edição do Censo Escolar.
