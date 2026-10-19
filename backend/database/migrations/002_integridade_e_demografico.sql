-- ============================================================
-- VELTIS - MIGRATION 002
-- Integridade, rastreabilidade, seguranca e tabela demografica unica
--
-- Aplicada pelo comando: python -m src.migrar
-- O executor roda este arquivo inteiro em UMA transacao:
-- se qualquer passo falhar, nada e alterado.
--
-- Preserva os dados ja carregados (municipios, SIDRA, escolas).
-- ============================================================


-- ============================================================
-- 0. VERIFICACOES DE SEGURANCA (antes de alterar qualquer coisa)
-- ============================================================

DO $$
BEGIN
    -- A tabela de classificacoes sera removida; ela precisa estar vazia.
    IF EXISTS (SELECT 1 FROM IBGE_DEMO_CLASSIF) THEN
        RAISE EXCEPTION
            'IBGE_DEMO_CLASSIF possui dados. Migration interrompida para nao perder informacao.';
    END IF;

    -- FONTE_DADOS vai receber UNIQUE (orgao, fonte).
    IF EXISTS (
        SELECT 1 FROM FONTE_DADOS
        GROUP BY NO_ORGAO, NO_FONTE HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION
            'FONTE_DADOS possui fontes duplicadas (mesmo orgao e nome). Corrija antes de migrar.';
    END IF;

    -- IBGE_DEMOGRAFICO vai receber UNIQUE pela identidade do valor.
    IF EXISTS (
        SELECT 1 FROM IBGE_DEMOGRAFICO
        GROUP BY CD_MUN, CO_PERIODO, CD_AGREGADO, CD_VARIAVEL HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION
            'IBGE_DEMOGRAFICO possui valores duplicados. Corrija antes de migrar.';
    END IF;
END $$;


-- ============================================================
-- 1. TABELA DEMOGRAFICA UNICA (ADR-002, opcao A)
--    IBGE_DEMOGRAFICO passa a guardar as classificacoes
--    (sexo, idade, etc.) na propria linha.
-- ============================================================

ALTER TABLE IBGE_DEMOGRAFICO
    ADD COLUMN DS_CHAVE_CLASSIFICACAO VARCHAR(200) NOT NULL DEFAULT '',
    ADD COLUMN JS_CLASSIFICACOES JSONB NOT NULL DEFAULT '[]'::JSONB,
    ADD COLUMN DS_VALOR_ORIGINAL VARCHAR(10);

COMMENT ON COLUMN IBGE_DEMOGRAFICO.DS_CHAVE_CLASSIFICACAO IS
    'Pares classificacao:categoria ordenados pelo id da classificacao, ex.: 2:4|287:93070. Vazio quando a tabela SIDRA nao tem classificacoes.';
COMMENT ON COLUMN IBGE_DEMOGRAFICO.JS_CLASSIFICACOES IS
    'Lista de objetos {cd_classificacao, no_classificacao, cd_categoria, no_categoria}.';
COMMENT ON COLUMN IBGE_DEMOGRAFICO.DS_VALOR_ORIGINAL IS
    'Simbolo especial do IBGE quando o valor nao e numerico: -, X, .., ...';

ALTER TABLE IBGE_DEMOGRAFICO
    ADD CONSTRAINT UQ_IBGE_DEMOGRAFICO_VALOR
    UNIQUE (CD_MUN, CO_PERIODO, CD_AGREGADO, CD_VARIAVEL, DS_CHAVE_CLASSIFICACAO);

ALTER TABLE IBGE_DEMOGRAFICO
    ADD CONSTRAINT CK_IBGE_DEMOGRAFICO_CLASSIF_ARRAY
    CHECK (JSONB_TYPEOF(JS_CLASSIFICACOES) = 'array');

DROP TABLE IBGE_DEMO_CLASSIF;


-- ============================================================
-- 2. INTEGRIDADE: chaves naturais que impedem duplicidade
-- ============================================================

ALTER TABLE FONTE_DADOS
    ADD CONSTRAINT UQ_FONTE_DADOS_ORGAO_FONTE
    UNIQUE (NO_ORGAO, NO_FONTE);

-- Uma oferta de curso = curso + dimensao geografica + municipio, por ano.
-- NULLS NOT DISTINCT (PostgreSQL 15+) trata municipio nulo como valor igual.
ALTER TABLE MEC_CURSOS
    ADD CONSTRAINT UQ_MEC_CURSOS_OFERTA
    UNIQUE NULLS NOT DISTINCT (NU_ANO_CENSO, CO_CURSO, TP_DIMENSAO, CO_MUNICIPIO);

-- Dominio oficial do Censo Superior 2024:
-- 1 presencial; 2 EAD por municipio; 3 EAD so nivel Brasil; 4 EAD no exterior.
ALTER TABLE MEC_CURSOS
    ADD CONSTRAINT CK_MEC_CURSOS_DIMENSAO
    CHECK (TP_DIMENSAO IN (1, 2, 3, 4));

-- Dimensoes 1 e 2 sempre tem municipio de oferta.
ALTER TABLE MEC_CURSOS
    ADD CONSTRAINT CK_MEC_CURSOS_MUNICIPIO_OFERTA
    CHECK (TP_DIMENSAO NOT IN (1, 2) OR CO_MUNICIPIO IS NOT NULL);


-- ============================================================
-- 3. RASTREABILIDADE: toda linha aponta para a carga que a gerou
-- ============================================================

ALTER TABLE IBGE_MUNICIPIOS    ADD COLUMN ID_INGESTAO BIGINT;
ALTER TABLE INEP_ESCOLA        ADD COLUMN ID_INGESTAO BIGINT;
ALTER TABLE INEP_CURSO_TECNICO ADD COLUMN ID_INGESTAO BIGINT;
ALTER TABLE MEC_IES            ADD COLUMN ID_INGESTAO BIGINT;
ALTER TABLE MEC_CURSOS         ADD COLUMN ID_INGESTAO BIGINT;

ALTER TABLE IBGE_MUNICIPIOS
    ADD CONSTRAINT FK_IBGE_MUNICIPIOS_INGESTAO
    FOREIGN KEY (ID_INGESTAO) REFERENCES CONTROLE_INGESTAO (ID_INGESTAO);

ALTER TABLE INEP_ESCOLA
    ADD CONSTRAINT FK_INEP_ESCOLA_INGESTAO
    FOREIGN KEY (ID_INGESTAO) REFERENCES CONTROLE_INGESTAO (ID_INGESTAO);

ALTER TABLE INEP_CURSO_TECNICO
    ADD CONSTRAINT FK_INEP_CURSO_TECNICO_INGESTAO
    FOREIGN KEY (ID_INGESTAO) REFERENCES CONTROLE_INGESTAO (ID_INGESTAO);

ALTER TABLE MEC_IES
    ADD CONSTRAINT FK_MEC_IES_INGESTAO
    FOREIGN KEY (ID_INGESTAO) REFERENCES CONTROLE_INGESTAO (ID_INGESTAO);

ALTER TABLE MEC_CURSOS
    ADD CONSTRAINT FK_MEC_CURSOS_INGESTAO
    FOREIGN KEY (ID_INGESTAO) REFERENCES CONTROLE_INGESTAO (ID_INGESTAO);

-- Liga os registros ja existentes a ultima carga concluida da sua fonte.
UPDATE IBGE_MUNICIPIOS SET ID_INGESTAO = (
    SELECT c.ID_INGESTAO
    FROM CONTROLE_INGESTAO c JOIN FONTE_DADOS f ON f.ID_FONTE = c.ID_FONTE
    WHERE f.NO_ORGAO = 'IBGE' AND f.NO_FONTE = 'Malha Municipal'
      AND c.DS_STATUS = 'CONCLUIDA'
    ORDER BY c.DT_PROCESSAMENTO DESC LIMIT 1)
WHERE ID_INGESTAO IS NULL;

UPDATE IBGE_DEMOGRAFICO d SET ID_INGESTAO = (
    SELECT c.ID_INGESTAO
    FROM CONTROLE_INGESTAO c JOIN FONTE_DADOS f ON f.ID_FONTE = c.ID_FONTE
    WHERE f.NO_ORGAO = 'IBGE' AND f.NO_FONTE = 'SIDRA'
      AND c.CO_PERIODO_REFERENCIA = d.CO_PERIODO
      AND c.DS_STATUS = 'CONCLUIDA'
    ORDER BY c.DT_PROCESSAMENTO DESC LIMIT 1)
WHERE d.ID_INGESTAO IS NULL;

UPDATE INEP_ESCOLA e SET ID_INGESTAO = (
    SELECT c.ID_INGESTAO
    FROM CONTROLE_INGESTAO c JOIN FONTE_DADOS f ON f.ID_FONTE = c.ID_FONTE
    WHERE f.NO_ORGAO = 'INEP' AND f.NO_FONTE = 'Censo Escolar'
      AND c.CO_PERIODO_REFERENCIA = e.NU_ANO_CENSO::TEXT
      AND c.DS_STATUS = 'CONCLUIDA'
    ORDER BY c.DT_PROCESSAMENTO DESC LIMIT 1)
WHERE e.ID_INGESTAO IS NULL;


-- ============================================================
-- 4. INDICES para as consultas mais comuns (ETL e API)
-- ============================================================

CREATE INDEX IDX_CONTROLE_INGESTAO_FONTE_HASH
    ON CONTROLE_INGESTAO (ID_FONTE, DS_HASH_SHA256);

CREATE INDEX IDX_IBGE_DEMOGRAFICO_AGREGADO
    ON IBGE_DEMOGRAFICO (CD_AGREGADO, CD_VARIAVEL, CO_PERIODO);

CREATE INDEX IDX_IBGE_DEMOGRAFICO_CLASSIF
    ON IBGE_DEMOGRAFICO USING GIN (JS_CLASSIFICACOES);

CREATE INDEX IDX_INEP_ESCOLA_MUNICIPIO
    ON INEP_ESCOLA (CO_MUNICIPIO);

CREATE INDEX IDX_INEP_CURSO_TECNICO_MUNICIPIO
    ON INEP_CURSO_TECNICO (CO_MUNICIPIO);

CREATE INDEX IDX_MEC_CURSOS_MUNICIPIO
    ON MEC_CURSOS (CO_MUNICIPIO);

CREATE INDEX IDX_MEC_CURSOS_IES
    ON MEC_CURSOS (NU_ANO_CENSO, CO_IES);


-- ============================================================
-- 5. SEGURANCA: Row Level Security em todas as tabelas
--    Sem politicas = a API automatica do Supabase (chave anon)
--    nao le nem altera nada. O backend (FastAPI e ETL) usa a
--    conexao direta do banco, que nao e afetada pelo RLS.
-- ============================================================

ALTER TABLE IBGE_MUNICIPIOS    ENABLE ROW LEVEL SECURITY;
ALTER TABLE IBGE_DEMOGRAFICO   ENABLE ROW LEVEL SECURITY;
ALTER TABLE INEP_ESCOLA        ENABLE ROW LEVEL SECURITY;
ALTER TABLE INEP_CURSO_TECNICO ENABLE ROW LEVEL SECURITY;
ALTER TABLE ESCOLA_LOCALIZACAO ENABLE ROW LEVEL SECURITY;
ALTER TABLE MEC_IES            ENABLE ROW LEVEL SECURITY;
ALTER TABLE MEC_CURSOS         ENABLE ROW LEVEL SECURITY;
ALTER TABLE FONTE_DADOS        ENABLE ROW LEVEL SECURITY;
ALTER TABLE CONTROLE_INGESTAO  ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- FIM DA MIGRATION 002
-- ============================================================
