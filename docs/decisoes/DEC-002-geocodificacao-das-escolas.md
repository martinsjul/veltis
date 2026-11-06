# DEC-002 — Geocodificação das escolas sem coordenada oficial

- **Estado:** aceita
- **Data:** 2026-11-03
- **Responsáveis pela decisão:** equipe do projeto
- **Relacionado a:** pipeline `geocodificacao`; migration `005_geocodificacao_escolas.sql`; `vw_escolas_mapa`; DEC-001

## Contexto

Cerca de 13% das escolas da RMS não têm latitude/longitude no Catálogo de Escolas do INEP nem na base Escolas Ativas da SEDUC-SP. Muitas delas têm endereço. Sem ponto, a escola não aparece no mapa.

## Alternativas consideradas

- **Não fazer nada:** as escolas ficam só na lista "sem localização". Simples, mas o mapa fica incompleto.
- **Google Geocoding:** preciso, mas pago acima da cota e os termos não permitem guardar as coordenadas no banco por mais de 30 dias nem exibi-las em mapa que não seja do Google.
- **OpenStreetMap (Nominatim público):** gratuito, mas limitado a 1 consulta por segundo e a política de uso desaconselha consultas em lote.
- **geocodebr (Ipea) sobre o CNEFE do IBGE:** gratuito, sem limite, roda localmente, dado oficial brasileiro (Censo 2022) e permite guardar o resultado citando a fonte; informa a precisão e a margem de erro de cada ponto.

## Decisão e justificativa

Usar o **geocodebr** (pacote Python do Ipea, licença MIT) como etapa automática do pipeline, só para as escolas **sem nenhuma coordenada oficial** e **com endereço**:

1. O endereço (Catálogo INEP ou SEDUC) é separado em logradouro, número, bairro e CEP.
2. O geocodebr procura o endereço no CNEFE e devolve o ponto, a precisão e a margem de erro (`desvio_metros`).
3. Só entram pontos com precisão `numero`/`numero_aproximado` (margem até 500 m) ou `logradouro` (até 1.000 m). Centro do CEP, do bairro ou do município é recusado.
4. Ponto fora do polígono do município da escola é descartado.
5. O ponto entra em `escola_localizacao` como fonte "IBGE - CNEFE 2022 - geocodificação", com `tp_metodo_localizacao = 'GEOCODIFICADO'`, `ds_precisao` e `vl_desvio_metros`.

A coordenada oficial tem sempre prioridade na `vw_escolas_mapa`. O endereço e o telefone exibidos continuam vindo das fontes oficiais.

## Consequências e revisão

- A API informa a origem do ponto em `precisaoLocalizacao` (`oficial`, `numero`, `numero_aproximado` ou `logradouro`), e o frontend pode diferenciar pontos aproximados.
- Escolas sem endereço, ou cujo endereço não foi encontrado com boa precisão, continuam sem ponto e aparecem em `/escolas/sem-localizacao`. Nada é inventado.
- Na primeira execução o geocodebr baixa os dados do CNEFE (~1 GB) para o cache do usuário.
- O pacote está em versão inicial (0.2.0, "alfa"); a versão fica fixada no `requirements.txt` e registrada em `controle_ingestao`.
- O site deve citar "IBGE, CNEFE – Censo Demográfico 2022" e "geocodebr (Ipea)".
- Revisar a cada nova edição do Censo Escolar: a etapa roda de novo e recalcula os pontos.
- Resultado da primeira execução no Supabase (2026-11-06): 43 das 198 escolas com endereço ganharam ponto; 155 foram recusadas por precisão insuficiente (ver `docs/testes/`, §4.5).
