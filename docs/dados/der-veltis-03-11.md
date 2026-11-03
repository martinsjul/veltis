# Diagrama de Entidade-Relacionamento — Veltis

> Modelo lógico baseado nas tabelas e restrições descritas na planilha **Veltis_Dicionario_de_Dados_Completo_2026-10-19.xlsx**.

## Figura X – Diagrama de Entidade-Relacionamento (Lógico)

```mermaid
erDiagram
    IBGE_MUNICIPIOS {
        char CD_MUN PK
        varchar NM_MUN
        varchar CD_RGI
        varchar NM_RGI
        varchar CD_RGINT
        varchar NM_RGINT
        varchar NM_UF
        char SIGLA_UF
        char CD_REGIAO
        varchar NM_REGIAO
        char SIGLA_RG
        char CD_CONCURB
        varchar NM_CONCURB
        numeric AREA_KM2
        geometry GEOMETRY
        bigint ID_INGESTAO FK
    }

    IBGE_DEMOGRAFICO {
        bigint ID_DEMOGRAFICO PK
        char CD_MUN FK
        varchar CO_PERIODO
        varchar CD_AGREGADO
        varchar CD_VARIAVEL
        varchar NO_VARIAVEL
        varchar DS_UNIDADE
        numeric VL_INDICADOR
        varchar DS_CHAVE_CLASSIFICACAO
        jsonb JS_CLASSIFICACOES
        varchar DS_VALOR_ORIGINAL
        bigint ID_INGESTAO FK
    }

    INEP_ESCOLA {
        smallint NU_ANO_CENSO PK
        integer CO_ENTIDADE PK
        varchar NO_ENTIDADE
        char CO_MUNICIPIO FK
        varchar NO_MUNICIPIO
        char SG_UF
        smallint TP_DEPENDENCIA
        smallint TP_LOCALIZACAO
        smallint TP_SITUACAO_FUNCIONAMENTO
        boolean IN_COMUM_MEDIO_MEDIO
        boolean IN_COMUM_MEDIO_INTEGRADO
        boolean IN_COMUM_MEDIO_FIC
        boolean IN_COMUM_MEDIO_NORMAL
        boolean IN_ITINERARIO_TECN_PROF
        bigint ID_INGESTAO FK
    }

    ESCOLA_LOCALIZACAO {
        bigint ID_LOCALIZACAO PK
        smallint NU_ANO_CENSO FK
        integer CO_ENTIDADE FK
        varchar DS_ENDERECO
        char NU_CEP
        varchar NU_TELEFONE
        numeric VL_LATITUDE
        numeric VL_LONGITUDE
        geometry GEOMETRY
        bigint ID_FONTE FK
        varchar TP_METODO_LOCALIZACAO
        bigint ID_INGESTAO FK
    }

    INEP_CURSO_TECNICO {
        smallint NU_ANO_CENSO PK
        integer CO_ENTIDADE PK
        integer CO_CURSO_EDUC_PROFISSIONAL PK
        char CO_MUNICIPIO FK
        varchar NO_MUNICIPIO
        varchar NO_CURSO_EDUC_PROFISSIONAL
        integer ID_AREA_CURSO_PROFISSIONAL
        varchar NO_AREA_CURSO_PROFISSIONAL
        integer QT_CURSO_TEC
        integer QT_MAT_CURSO_TEC
        bigint ID_INGESTAO FK
    }

    MEC_IES {
        smallint NU_ANO_CENSO PK
        integer CO_IES PK
        varchar NO_IES
        varchar SG_IES
        char CO_MUNICIPIO_IES
        varchar NO_MUNICIPIO_IES
        char SG_UF_IES
        smallint TP_ORGANIZACAO_ACADEMICA
        smallint TP_REDE
        smallint TP_CATEGORIA_ADMINISTRATIVA
        varchar DS_ENDERECO_IES
        varchar NO_BAIRRO_IES
        char NU_CEP_IES
        bigint ID_INGESTAO FK
    }

    MEC_CURSOS {
        bigint ID_OFERTA_CURSO PK
        smallint NU_ANO_CENSO FK
        smallint TP_DIMENSAO
        integer CO_IES FK
        integer CO_CURSO
        varchar NO_CURSO
        char CO_MUNICIPIO FK
        varchar NO_MUNICIPIO
        char SG_UF
        varchar NO_CINE_AREA_GERAL
        varchar NO_CINE_AREA_ESPECIFICA
        smallint TP_GRAU_ACADEMICO
        boolean IN_GRATUITO
        smallint TP_MODALIDADE_ENSINO
        smallint TP_NIVEL_ACADEMICO
        integer QT_CURSO
        integer QT_VG_TOTAL
        integer QT_MAT
        bigint ID_INGESTAO FK
    }

    FONTE_DADOS {
        bigint ID_FONTE PK
        varchar NO_ORGAO
        varchar NO_FONTE
        text DS_URL_OFICIAL
        varchar DS_PERIODICIDADE
        varchar DS_TIPO_FONTE
        text DS_OBSERVACAO
    }

    CONTROLE_INGESTAO {
        bigint ID_INGESTAO PK
        bigint ID_FONTE FK
        varchar CO_PERIODO_REFERENCIA
        varchar DS_VERSAO
        varchar NO_ARQUIVO_ORIGEM
        date DT_OBTENCAO
        timestamp DT_PROCESSAMENTO
        char DS_HASH_SHA256
        bigint QT_REGISTROS_LIDOS
        bigint QT_REGISTROS_CARREGADOS
        bigint QT_REGISTROS_REJEITADOS
        varchar DS_STATUS
        text DS_OBSERVACAO
    }

    IBGE_MUNICIPIOS ||--o{ IBGE_DEMOGRAFICO : "possui indicadores"
    IBGE_MUNICIPIOS ||--o{ INEP_ESCOLA : "localiza escolas"
    IBGE_MUNICIPIOS ||--o{ INEP_CURSO_TECNICO : "localiza ofertas tecnicas"
    IBGE_MUNICIPIOS ||--o{ MEC_CURSOS : "localiza ofertas superiores"

    INEP_ESCOLA ||--o{ ESCOLA_LOCALIZACAO : "possui localizacoes"
    INEP_ESCOLA ||--o{ INEP_CURSO_TECNICO : "oferta cursos tecnicos"

    MEC_IES ||--o{ MEC_CURSOS : "oferta cursos superiores"

    FONTE_DADOS ||--o{ CONTROLE_INGESTAO : "identifica a fonte"
    FONTE_DADOS ||--o{ ESCOLA_LOCALIZACAO : "origina localizacao"

    CONTROLE_INGESTAO o|--o{ IBGE_MUNICIPIOS : "origina carga"
    CONTROLE_INGESTAO o|--o{ IBGE_DEMOGRAFICO : "origina carga"
    CONTROLE_INGESTAO o|--o{ INEP_ESCOLA : "origina carga"
    CONTROLE_INGESTAO o|--o{ ESCOLA_LOCALIZACAO : "origina carga"
    CONTROLE_INGESTAO o|--o{ INEP_CURSO_TECNICO : "origina carga"
    CONTROLE_INGESTAO o|--o{ MEC_IES : "origina carga"
    CONTROLE_INGESTAO o|--o{ MEC_CURSOS : "origina carga"
```

<div align="center">
<sub><b>Fonte:</b> Elaborado pelos autores com base no Dicionário de Dados do Veltis.</sub>
</div>

## Descrição dos relacionamentos

- **IBGE_MUNICIPIOS — IBGE_DEMOGRAFICO (1:N):** um município pode possuir vários registros de indicadores, referentes a períodos, agregados, variáveis e classificações diferentes. Cada registro demográfico pertence a um município.
- **IBGE_MUNICIPIOS — INEP_ESCOLA (1:N):** um município pode possuir várias escolas. Cada registro de escola está associado a um município pelo código IBGE.
- **IBGE_MUNICIPIOS — INEP_CURSO_TECNICO (1:N):** os registros de cursos técnicos são associados ao município informado na base do Censo Escolar.
- **IBGE_MUNICIPIOS — MEC_CURSOS (1:N):** os cursos superiores são associados ao município do local de oferta quando esse dado está disponível. O município da sede da IES não substitui o município de oferta.
- **INEP_ESCOLA — ESCOLA_LOCALIZACAO (1:N):** uma escola pode possuir registros de localização provenientes de fontes diferentes. A ligação utiliza o ano do Censo e o código da entidade.
- **INEP_ESCOLA — INEP_CURSO_TECNICO (1:N):** uma escola pode ofertar vários cursos técnicos. A relação utiliza o ano do Censo e o código da entidade.
- **MEC_IES — MEC_CURSOS (1:N):** uma instituição de ensino superior pode ofertar vários cursos. A identificação da IES utiliza o ano do Censo e o código da IES.
- **FONTE_DADOS — CONTROLE_INGESTAO (1:N):** uma fonte pode possuir várias execuções de carga registradas.
- **FONTE_DADOS — ESCOLA_LOCALIZACAO (1:N):** cada registro de localização identifica a fonte de onde vieram o endereço e/ou as coordenadas.
- **CONTROLE_INGESTAO — tabelas de dados (1:N):** uma execução de carga pode originar vários registros nas tabelas de dados. O vínculo é feito pelo campo `ID_INGESTAO`, que pode estar nulo conforme a definição da planilha.

## Observações sobre o modelo

1. `IBGE_DEMO_CLASSIF` não aparece no diagrama porque foi removida na migration 002. As classificações e categorias do SIDRA são armazenadas em `IBGE_DEMOGRAFICO`, nos campos `DS_CHAVE_CLASSIFICACAO` e `JS_CLASSIFICACOES`.
2. `MEC_IES` armazena a instituição e o município de sua sede. `MEC_CURSOS` armazena as ofertas e o município do local de oferta. Uma IES sediada fora da Região Metropolitana de Sorocaba pode ofertar cursos em municípios da região.
3. `ESCOLA_LOCALIZACAO` separa os dados de endereço e coordenadas dos dados cadastrais da escola. Assim, uma escola pode continuar cadastrada mesmo quando não possui coordenadas.
4. Os campos `ID_INGESTAO` permitem rastrear a carga de origem dos registros. A planilha informa que esses campos podem ser nulos.
5. O diagrama representa as relações descritas no dicionário. Restrições identificadas na planilha como sugeridas ou lógicas devem ser confirmadas no DDL do PostgreSQL antes de serem tratadas como restrições físicas implementadas.
