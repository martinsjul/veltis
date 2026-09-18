-- ============================================================================
-- VELTIS
-- Banco de Dados - PostgreSQL + PostGIS
--
-- Projeto Integrador - FATEC Sorocaba
-- Região Metropolitana de Sorocaba (RMS)
--
-- Fontes utilizadas no projeto:
--   IBGE
--   Censo Escolar / INEP
--   Censo da Educação Superior / INEP
--
-- Estrutura principal:
--   1. IBGE_MUNICIPIOS
--   2. IBGE_DEMOGRAFICO
--   3. INEP_ESCOLA
--   4. INEP_CURSO_TECNICO
--   5. MEC_IES
--   6. MEC_CURSOS
-- ============================================================================


-- ============================================================================
-- POSTGIS
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS postgis;


-- ============================================================================
-- 1. IBGE_MUNICIPIOS
--
-- Malha municipal utilizada pelo Veltis.
-- A geometria permitirá a representação dos municípios no mapa.
-- ============================================================================

CREATE TABLE IBGE_MUNICIPIOS (

    CD_MUN          CHAR(7) NOT NULL,
    NM_MUN          VARCHAR(100) NOT NULL,

    CD_RGI          CHAR(6),
    NM_RGI          VARCHAR(100),

    CD_RGINT        CHAR(4),
    NM_RGINT        VARCHAR(100),

    CD_UF           CHAR(2),
    NM_UF           VARCHAR(50),
    SIGLA_UF        CHAR(2),

    CD_REGIAO       CHAR(1),
    NM_REGIAO       VARCHAR(30),
    SIGLA_RG        CHAR(2),

    CD_CONCURB      CHAR(7),
    NM_CONCURB      VARCHAR(100),

    AREA_KM2        DECIMAL(12,3),

    geometry        GEOMETRY(MULTIPOLYGON, 4674) NOT NULL,

    CONSTRAINT PK_IBGE_MUNICIPIOS
        PRIMARY KEY (CD_MUN),

    CONSTRAINT CHK_IBGE_MUNICIPIOS_AREA
        CHECK (
            AREA_KM2 IS NULL
            OR AREA_KM2 >= 0
        )
);


-- ============================================================================
-- 2. IBGE_DEMOGRAFICO
--
-- Indicadores demográficos associados aos municípios.
--
-- CD_AGREGADO identifica a tabela/agregado de origem no SIDRA.
-- CD_VARIAVEL identifica a variável consultada.
-- ============================================================================

CREATE TABLE IBGE_DEMOGRAFICO (

    ID_DEMOGRAFICO
        BIGINT GENERATED ALWAYS AS IDENTITY,

    CD_MUN
        CHAR(7) NOT NULL,

    NU_ANO_CENSO
        INTEGER NOT NULL,

    CD_AGREGADO
        VARCHAR(12) NOT NULL,

    CD_VARIAVEL
        VARCHAR(20) NOT NULL,

    VL_INDICADOR
        DECIMAL(20,6),

    CONSTRAINT PK_IBGE_DEMOGRAFICO
        PRIMARY KEY (ID_DEMOGRAFICO),

    CONSTRAINT FK_IBGE_DEMOGRAFICO_MUNICIPIO
        FOREIGN KEY (CD_MUN)
        REFERENCES IBGE_MUNICIPIOS (CD_MUN),

    CONSTRAINT UQ_IBGE_DEMOGRAFICO
        UNIQUE (
            CD_MUN,
            NU_ANO_CENSO,
            CD_AGREGADO,
            CD_VARIAVEL
        )
);


-- ============================================================================
-- 3. INEP_ESCOLA
--
-- Escolas do Censo Escolar.
--
-- A chave é composta por:
--   NU_ANO_CENSO
--   CO_ENTIDADE
--
-- Isso permite armazenar a mesma escola em diferentes anos de Censo.
--
-- Os campos de endereço foram mantidos como opcionais porque não devem ser
-- considerados garantidos pela fonte pública 2025 analisada.
-- ============================================================================

CREATE TABLE INEP_ESCOLA (

    NU_ANO_CENSO
        INTEGER NOT NULL,

    CO_ENTIDADE
        INTEGER NOT NULL,

    NO_ENTIDADE
        VARCHAR(255) NOT NULL,

    CO_MUNICIPIO
        CHAR(7) NOT NULL,

    NO_MUNICIPIO
        VARCHAR(150) NOT NULL,

    SG_UF
        CHAR(2) NOT NULL,

    TP_DEPENDENCIA
        SMALLINT NOT NULL,

    TP_LOCALIZACAO
        SMALLINT NOT NULL,


    -- ------------------------------------------------------------------------
    -- ENDEREÇO
    -- Opcionais na estrutura atual
    -- ------------------------------------------------------------------------

    DS_ENDERECO
        VARCHAR(255),

    NO_BAIRRO
        VARCHAR(100),

    CO_CEP
        CHAR(8),

    NU_TELEFONE
        VARCHAR(20),

    LATITUDE
        DECIMAL(20,16),

    LONGITUDE
        DECIMAL(20,16),


    -- ------------------------------------------------------------------------
    -- SITUAÇÃO DA ESCOLA
    -- ------------------------------------------------------------------------

    TP_SITUACAO_FUNCIONAMENTO
        SMALLINT NOT NULL,


    -- ------------------------------------------------------------------------
    -- ENSINO MÉDIO
    -- ------------------------------------------------------------------------

    IN_COMUM_MEDIO_MEDIO
        BOOLEAN,

    IN_COMUM_MEDIO_INTEGRADO
        BOOLEAN,

    IN_COMUM_MEDIO_FIC
        BOOLEAN,

    IN_COMUM_MEDIO_NORMAL
        BOOLEAN,

    IN_ITINERARIO_TECN_PROF
        BOOLEAN,


    CONSTRAINT PK_INEP_ESCOLA
        PRIMARY KEY (
            NU_ANO_CENSO,
            CO_ENTIDADE
        ),


    CONSTRAINT FK_INEP_ESCOLA_MUNICIPIO
        FOREIGN KEY (CO_MUNICIPIO)
        REFERENCES IBGE_MUNICIPIOS (CD_MUN),


    CONSTRAINT CHK_INEP_ESCOLA_DEPENDENCIA
        CHECK (
            TP_DEPENDENCIA IN (1, 2, 3, 4)
        ),


    CONSTRAINT CHK_INEP_ESCOLA_LOCALIZACAO
        CHECK (
            TP_LOCALIZACAO IN (1, 2)
        )
);


-- ============================================================================
-- 4. INEP_CURSO_TECNICO
--
-- Cursos técnicos presentes no Censo Escolar.
--
-- Associação:
--
--      INEP_ESCOLA
--          |
--          | NU_ANO_CENSO + CO_ENTIDADE
--          |
--          v
--      INEP_CURSO_TECNICO
--
-- Uma escola pode possuir vários cursos técnicos.
-- ============================================================================

CREATE TABLE INEP_CURSO_TECNICO (

    NU_ANO_CENSO
        INTEGER NOT NULL,

    CO_ENTIDADE
        INTEGER NOT NULL,

    CO_MUNICIPIO
        CHAR(7) NOT NULL,

    NO_MUNICIPIO
        VARCHAR(150) NOT NULL,


    -- ------------------------------------------------------------------------
    -- CURSO
    -- ------------------------------------------------------------------------

    CO_CURSO_EDUC_PROFISSIONAL
        INTEGER NOT NULL,

    NO_CURSO_EDUC_PROFISSIONAL
        VARCHAR(255) NOT NULL,


    -- ------------------------------------------------------------------------
    -- ÁREA DO CURSO
    -- ------------------------------------------------------------------------

    ID_AREA_CURSO_PROFISSIONAL
        INTEGER,

    NO_AREA_CURSO_PROFISSIONAL
        VARCHAR(255),


    -- ------------------------------------------------------------------------
    -- QUANTIDADES
    -- ------------------------------------------------------------------------

    QT_CURSO_TEC
        INTEGER,

    QT_MAT_CURSO_TEC
        INTEGER,


    CONSTRAINT PK_INEP_CURSO_TECNICO
        PRIMARY KEY (
            NU_ANO_CENSO,
            CO_ENTIDADE,
            CO_CURSO_EDUC_PROFISSIONAL
        ),


    CONSTRAINT FK_INEP_CURSO_TECNICO_ESCOLA
        FOREIGN KEY (
            NU_ANO_CENSO,
            CO_ENTIDADE
        )
        REFERENCES INEP_ESCOLA (
            NU_ANO_CENSO,
            CO_ENTIDADE
        ),


    CONSTRAINT FK_INEP_CURSO_TECNICO_MUNICIPIO
        FOREIGN KEY (CO_MUNICIPIO)
        REFERENCES IBGE_MUNICIPIOS (CD_MUN),


    CONSTRAINT CHK_INEP_CURSO_TECNICO_QT
        CHECK (
            QT_CURSO_TEC IS NULL
            OR QT_CURSO_TEC >= 0
        ),


    CONSTRAINT CHK_INEP_CURSO_TECNICO_MATRICULAS
        CHECK (
            QT_MAT_CURSO_TEC IS NULL
            OR QT_MAT_CURSO_TEC >= 0
        )
);


-- ============================================================================
-- 5. MEC_IES
--
-- Instituições de Educação Superior.
--
-- IMPORTANTE:
--
-- CO_MUNICIPIO_IES representa o MUNICÍPIO DA SEDE da instituição.
--
-- Ele NÃO possui FK para IBGE_MUNICIPIOS.
--
-- Motivo:
-- uma IES pode possuir sede fora da Região Metropolitana de Sorocaba
-- e mesmo assim possuir oferta de curso dentro da RMS.
--
-- Exemplo da associação:
--
-- MEC_IES.CO_IES
--       |
--       v
-- MEC_CURSOS.CO_IES
-- ============================================================================

CREATE TABLE MEC_IES (

    NU_ANO_CENSO
        INTEGER NOT NULL,

    CO_IES
        INTEGER NOT NULL,

    NO_IES
        VARCHAR(255) NOT NULL,

    SG_IES
        VARCHAR(50),


    -- ------------------------------------------------------------------------
    -- MUNICÍPIO DA SEDE
    -- ------------------------------------------------------------------------

    CO_MUNICIPIO_IES
        CHAR(7) NOT NULL,

    NO_MUNICIPIO_IES
        VARCHAR(150) NOT NULL,

    SG_UF_IES
        CHAR(2) NOT NULL,


    -- ------------------------------------------------------------------------
    -- CLASSIFICAÇÃO DA IES
    -- ------------------------------------------------------------------------

    TP_ORGANIZACAO_ACADEMICA
        SMALLINT NOT NULL,

    TP_REDE
        SMALLINT NOT NULL,

    TP_CATEGORIA_ADMINISTRATIVA
        SMALLINT NOT NULL,


    -- ------------------------------------------------------------------------
    -- ENDEREÇO
    -- ------------------------------------------------------------------------

    DS_ENDERECO_IES
        VARCHAR(255),

    NO_BAIRRO_IES
        VARCHAR(100),

    NU_CEP_IES
        CHAR(8),


    CONSTRAINT PK_MEC_IES
        PRIMARY KEY (
            NU_ANO_CENSO,
            CO_IES
        ),


    CONSTRAINT CHK_MEC_IES_ORGANIZACAO
        CHECK (
            TP_ORGANIZACAO_ACADEMICA
            IN (1, 2, 3, 4, 5)
        ),


    CONSTRAINT CHK_MEC_IES_REDE
        CHECK (
            TP_REDE IN (1, 2)
        ),


    CONSTRAINT CHK_MEC_IES_CATEGORIA
        CHECK (
            TP_CATEGORIA_ADMINISTRATIVA
            IN (1, 2, 3, 4, 5, 7)
        )
);


-- ============================================================================
-- 6. MEC_CURSOS
--
-- Cursos da Educação Superior.
--
-- IMPORTANTE:
--
-- CO_MUNICIPIO nesta tabela representa o LOCAL DA OFERTA DO CURSO.
--
-- Portanto:
--
-- MEC_IES.CO_MUNICIPIO_IES
--     = município da sede da instituição
--
-- MEC_CURSOS.CO_MUNICIPIO
--     = município onde o curso é ofertado
--
-- Para o Veltis, o segundo é essencial para relacionar a oferta de cursos
-- aos municípios da RMS.
--
-- Os registros territoriais carregados nesta tabela devem possuir
-- CO_MUNICIPIO definido.
-- ============================================================================

CREATE TABLE MEC_CURSOS (

    NU_ANO_CENSO
        INTEGER NOT NULL,

    TP_DIMENSAO
        SMALLINT NOT NULL,


    -- ------------------------------------------------------------------------
    -- IES
    -- ------------------------------------------------------------------------

    CO_IES
        INTEGER NOT NULL,


    -- ------------------------------------------------------------------------
    -- CURSO
    -- ------------------------------------------------------------------------

    CO_CURSO
        INTEGER NOT NULL,

    NO_CURSO
        VARCHAR(255) NOT NULL,


    -- ------------------------------------------------------------------------
    -- LOCAL DA OFERTA
    -- ------------------------------------------------------------------------

    CO_MUNICIPIO
        CHAR(7) NOT NULL,

    NO_MUNICIPIO
        VARCHAR(150) NOT NULL,

    SG_UF
        CHAR(2),


    -- ------------------------------------------------------------------------
    -- CLASSIFICAÇÃO CINE
    -- ------------------------------------------------------------------------

    NO_CINE_AREA_GERAL
        VARCHAR(150),

    NO_CINE_AREA_ESPECIFICA
        VARCHAR(150),


    -- ------------------------------------------------------------------------
    -- CARACTERÍSTICAS ACADÊMICAS
    -- ------------------------------------------------------------------------

    TP_GRAU_ACADEMICO
        SMALLINT,

    TP_MODALIDADE_ENSINO
        SMALLINT NOT NULL,

    TP_NIVEL_ACADEMICO
        SMALLINT,


    -- ------------------------------------------------------------------------
    -- QUANTIDADES
    -- ------------------------------------------------------------------------

    QT_CURSO
        INTEGER,

    QT_VG_TOTAL
        INTEGER,

    QT_MAT
        INTEGER,


    -- ------------------------------------------------------------------------
    -- GRATUIDADE
    -- ------------------------------------------------------------------------

    IN_GRATUITO
        BOOLEAN,


    CONSTRAINT PK_MEC_CURSOS
        PRIMARY KEY (
            NU_ANO_CENSO,
            TP_DIMENSAO,
            CO_IES,
            CO_CURSO,
            CO_MUNICIPIO,
            TP_MODALIDADE_ENSINO
        ),


    CONSTRAINT FK_MEC_CURSOS_IES
        FOREIGN KEY (
            NU_ANO_CENSO,
            CO_IES
        )
        REFERENCES MEC_IES (
            NU_ANO_CENSO,
            CO_IES
        ),


    CONSTRAINT FK_MEC_CURSOS_MUNICIPIO
        FOREIGN KEY (CO_MUNICIPIO)
        REFERENCES IBGE_MUNICIPIOS (CD_MUN),


    CONSTRAINT CHK_MEC_CURSOS_MODALIDADE
        CHECK (
            TP_MODALIDADE_ENSINO IN (1, 2)
        ),


    CONSTRAINT CHK_MEC_CURSOS_QT
        CHECK (
            QT_CURSO IS NULL
            OR QT_CURSO >= 0
        ),


    CONSTRAINT CHK_MEC_CURSOS_VAGAS
        CHECK (
            QT_VG_TOTAL IS NULL
            OR QT_VG_TOTAL >= 0
        ),


    CONSTRAINT CHK_MEC_CURSOS_MATRICULAS
        CHECK (
            QT_MAT IS NULL
            OR QT_MAT >= 0
        )
);


-- ============================================================================
-- ÍNDICES
--
-- Os índices abaixo ajudam principalmente nos filtros, JOINs e consultas
-- utilizadas pelo Veltis.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- IBGE - GEOMETRIA
-- ----------------------------------------------------------------------------

CREATE INDEX IDX_IBGE_MUNICIPIOS_GEOMETRY
    ON IBGE_MUNICIPIOS
    USING GIST (geometry);


-- ----------------------------------------------------------------------------
-- IBGE - DEMOGRÁFICO
-- ----------------------------------------------------------------------------

CREATE INDEX IDX_IBGE_DEMOGRAFICO_MUNICIPIO
    ON IBGE_DEMOGRAFICO (CD_MUN);


CREATE INDEX IDX_IBGE_DEMOGRAFICO_ANO
    ON IBGE_DEMOGRAFICO (NU_ANO_CENSO);


CREATE INDEX IDX_IBGE_DEMOGRAFICO_VARIAVEL
    ON IBGE_DEMOGRAFICO (CD_VARIAVEL);


-- ----------------------------------------------------------------------------
-- INEP - ESCOLAS
-- ----------------------------------------------------------------------------

CREATE INDEX IDX_INEP_ESCOLA_MUNICIPIO
    ON INEP_ESCOLA (CO_MUNICIPIO);


CREATE INDEX IDX_INEP_ESCOLA_NOME
    ON INEP_ESCOLA (NO_ENTIDADE);


CREATE INDEX IDX_INEP_ESCOLA_DEPENDENCIA
    ON INEP_ESCOLA (TP_DEPENDENCIA);


-- ----------------------------------------------------------------------------
-- INEP - CURSOS TÉCNICOS
-- ----------------------------------------------------------------------------

CREATE INDEX IDX_INEP_CURSO_TECNICO_ESCOLA
    ON INEP_CURSO_TECNICO (
        NU_ANO_CENSO,
        CO_ENTIDADE
    );


CREATE INDEX IDX_INEP_CURSO_TECNICO_MUNICIPIO
    ON INEP_CURSO_TECNICO (CO_MUNICIPIO);


CREATE INDEX IDX_INEP_CURSO_TECNICO_CURSO
    ON INEP_CURSO_TECNICO (
        CO_CURSO_EDUC_PROFISSIONAL
    );


-- ----------------------------------------------------------------------------
-- MEC - IES
-- ----------------------------------------------------------------------------

CREATE INDEX IDX_MEC_IES_MUNICIPIO_SEDE
    ON MEC_IES (CO_MUNICIPIO_IES);


CREATE INDEX IDX_MEC_IES_NOME
    ON MEC_IES (NO_IES);


-- ----------------------------------------------------------------------------
-- MEC - CURSOS
-- ----------------------------------------------------------------------------

CREATE INDEX IDX_MEC_CURSOS_IES
    ON MEC_CURSOS (
        NU_ANO_CENSO,
        CO_IES
    );


CREATE INDEX IDX_MEC_CURSOS_MUNICIPIO
    ON MEC_CURSOS (CO_MUNICIPIO);


CREATE INDEX IDX_MEC_CURSOS_CURSO
    ON MEC_CURSOS (CO_CURSO);


CREATE INDEX IDX_MEC_CURSOS_NOME
    ON MEC_CURSOS (NO_CURSO);


CREATE INDEX IDX_MEC_CURSOS_MODALIDADE
    ON MEC_CURSOS (TP_MODALIDADE_ENSINO);


-- ============================================================================
-- FIM
-- ============================================================================