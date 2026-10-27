# Veltis

O **Veltis** é um Projeto Integrador acadêmico (ADS, Fatec Sorocaba) que integra dados públicos oficiais da Região Metropolitana de Sorocaba (RMS), composta por 27 municípios, para um portal web com mapa, filtros e indicadores.

- **Equipe:** Julia Ribeiro Martins (backend) e Daniel Lansana de Almeida (frontend)
- **Orientador:** prof. Munari

## Estado atual

| Parte | Situação |
| --- | --- |
| Banco PostgreSQL/PostGIS (Supabase) | Schema versionado em migrations (001 a 003) |
| Pipelines de dados | 5 coletores, que alimentam as 9 tabelas de dados e rodam na ordem certa com um comando |
| Views de leitura para a API | Prontas (geometrias em EPSG:4326, códigos traduzidos) |
| Testes | 41 testes unitários + 6 de integração com o banco |
| API (FastAPI) | Próxima fase |
| Frontend (React + Leaflet) | Próxima fase |

## Fontes e tabelas

| # | Pipeline | Fonte oficial | Edição | Tabelas |
| --- | --- | --- | --- | --- |
| 1 | `ibge_malha` | IBGE, Malha Municipal | 2025 | `ibge_municipios` |
| 2 | `sidra` | IBGE, SIDRA (API v3) | Censo 2022 + estimativas 2024–2026 | `ibge_demografico` |
| 3 | `censo_escolar` | INEP, Censo Escolar | 2025 V2 | `inep_escola`, `inep_curso_tecnico` |
| 4 | `localizacao_escolas` | INEP Catálogo de Escolas + SEDUC-SP | exportação manual | `escola_localizacao` |
| 5 | `censo_superior` | INEP, Censo da Educação Superior | 2024 | `mec_ies`, `mec_cursos` |

Toda carga fica registrada em `fonte_dados` e `controle_ingestao`: arquivo, hash SHA-256, contagens e status (`INICIADA`, `CONCLUIDA` ou `FALHA`). Cada linha de dados guarda o `id_ingestao` da carga que a gerou.

As edições ficam fixas em `backend/src/config/edicoes.py`. Rodar de novo produz o mesmo banco; para atualizar uma fonte, mude o ano ali.

## Estrutura

```text
backend/
├── database/migrations/   001 schema inicial · 002 integridade + demografia única · 003 views
├── certs/                 certificado intermediário do INEP (ver "Download do INEP")
├── data/
│   ├── raw/               arquivos oficiais (não versionados)
│   │   ├── ibge/  inep/censo_escolar/  inep/censo_superior/   ← baixados automaticamente
│   │   └── inep/catalogo_escolas/  seduc_sp/                  ← colocados à mão
│   └── processed/
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
docs/                      dicionário de dados, metadados e fontes
frontend/                  aplicação React (próxima fase)
```

## Configuração local

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

### Download do INEP

O servidor `download.inep.gov.br` não envia o certificado intermediário da sua cadeia TLS, então downloads comuns falham com `unable to get local issuer certificate`. O projeto inclui esse intermediário em `backend/certs/` e o soma às autoridades padrão (certifi) só para o INEP. A verificação de segurança **nunca** é desligada.

- Certificado: RNP ICPEdu GR46 OV TLS CA 2025, emitido por GlobalSign Root R46.
- Validade: até 19/11/2030.
- SHA-256: `E1:07:47:D4:DA:7B:AB:09:CB:A9:95:2F:01:9D:35:34:CB:9F:BA:07:0B:F1:3D:87:91:B1:69:9C:D2:FF:59:DD`

## Views para a API

| View | Conteúdo |
| --- | --- |
| `vw_municipios_mapa` | Contorno dos 27 municípios (EPSG:4326) + população 2022 |
| `vw_indicadores_municipio` | Uma linha por município: população, sexo, faixas de idade, alfabetização, frequência escolar, instrução |
| `vw_escolas_mapa` | Uma linha por escola, com a melhor localização disponível, rótulos em texto e coordenadas em EPSG:4326 |
| `vw_cursos_tecnicos` | Cursos de educação profissional por escola |
| `vw_cursos_superiores` | Ofertas de graduação por município de oferta, com a IES |
| `vw_ultimas_cargas` | Auditoria: última carga de cada arquivo |

## Testes

```bash
pytest                    # testes unitários (sem banco e sem internet)
```

Os testes de integração precisam de um banco PostgreSQL + PostGIS **vazio e descartável** (nunca o Supabase):

```bash
VELTIS_TESTE_DATABASE_URL=postgresql+psycopg://postgres:senha@localhost:5432/veltis_teste pytest
```

## Regras de dados

- O Censo Escolar define o universo de escolas. Catálogo e SEDUC só enriquecem.
- Coordenada ausente fica `NULL`. Nada é inventado, e coordenada oficial é diferente de geocodificada.
- O município do curso superior é o **local de oferta**, não a sede da IES.
- No SIDRA, as categorias são pedidas explicitamente: `[all]` mistura níveis e conta em dobro.
- Taxas não se somam entre municípios.
