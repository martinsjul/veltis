# Dados do Veltis

- [DER — Diagrama de Entidade-Relacionamento](der-veltis-03-11.md)
- [Dicionário de dados (planilha)](Veltis_Dicionario_de_Dados_Completo_2026-11-03.xlsx): cada tabela e coluna, tipo, restrições, domínio, origem e exemplo; domínios; validações; views.
- Documentos de referência de setembro de 2026 (histórico): `Veltis_Bases_e_Fontes_de_Dados_Revisado_2026-09-24.docx` e `Veltis_Metadados_Revisado_2026-09-24.docx`. Em caso de diferença, valem este README, o DER e o dicionário de 2026-11-03.

## Fontes e proveniência

Todos os dados são públicos e agregados por município ou instituição; nenhum dado pessoal é usado.

| Conjunto | Responsável / URL | Edição e cobertura | Condição de uso | Como chega ao Veltis |
| --- | --- | --- | --- | --- |
| Malha Municipal | IBGE — https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html | 2025; municípios de SP, filtrados para os 27 da RMS | Dado público; citar IBGE | Download automático (etapa `malha`) |
| Agregados do Censo 2022 e estimativas | IBGE — API SIDRA v3, https://servicodados.ibge.gov.br/api/docs/agregados?versao=3 | Censo 2022 (tabelas 4709, 4714, 9514, 9542, 10056, 10061) e estimativas 2024–2026 (6579) | Dado público; citar IBGE | API (etapa `sidra`) |
| Censo Escolar (microdados) | INEP — https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar | 2025 (versão 2); escolas e cursos técnicos | Dado público; citar INEP | Download automático (etapa `censo_escolar`) |
| Catálogo de Escolas | INEP — https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/inep-data/catalogo-de-escolas | Exportação de 2026-10-19 (SP) | Dado público; citar INEP | Exportação manual para `backend/data/raw/inep/catalogo_escolas/` (etapa `localizacao`) |
| Escolas Ativas | SEDUC-SP — https://dados.educacao.sp.gov.br/dataset/escolas-ativas | Arquivo de endereços de jun/2025; redes estadual, municipal e federal | Dado aberto; citar SEDUC-SP | Download manual para `backend/data/raw/seduc_sp/` (etapa `localizacao`) |
| CNEFE (endereços com coordenadas) | IBGE, via pacote geocodebr do Ipea — https://github.com/ipea/geocodebr | Censo 2022 | Dado público (IBGE) e pacote MIT; citar IBGE e Ipea | Etapa `geocodificacao` (só escolas sem coordenada oficial) |
| Censo da Educação Superior (microdados) | INEP — https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior | 2024; instituições e cursos | Dado público; citar INEP | Download automático (etapa `censo_superior`) |
| Locais (campi) das faculdades | Levantamento da equipe: endereço do INEP ou do site da instituição; coordenada do OpenStreetMap ou do CNEFE | 39 campi presenciais, consulta em 2026-10-28 e 2026-11-03 | OpenStreetMap: ODbL, citar "© OpenStreetMap contributors" | Arquivo versionado `backend/data/referencia/ies_locais_oferta.csv` (etapa `locais_ies`) |

Recorte territorial: 27 municípios da RMS (Lei Complementar estadual 1.241/2014, com a inclusão de Itapetininga pela LC 1.289/2016), definidos em `backend/src/config/rms.py`.

## Organização e reprodução

- **Arquivos baixados** ficam em `backend/data/raw/` e **não** são versionados (são grandes e reproduzíveis). As edições estão fixas em `backend/src/config/edicoes.py`.
- **Transformações:** feitas pelos pipelines em `backend/src/` (recorte da RMS, conversão de códigos, validação de domínios e duplicidade). Cada carga registra arquivo, hash SHA-256 e contagens em `CONTROLE_INGESTAO`.
- **Execução:** `python -m src.pipeline` dentro de `backend/` (ver [`backend/README.md`](../../backend/README.md)).
- **Resultados da última carga verificada:** `docs/testes/plano-e-evidencias-de-testes.md` §4.2.
