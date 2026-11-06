-- ============================================================
-- VELTIS - MIGRATION 004
-- Coordenadas das faculdades (locais de oferta presencial) e
-- view única para o mapa (escolas + faculdades com latitude/longitude).
--
-- Por quê: o Censo da Educação Superior (INEP) só traz o endereço da
-- SEDE de cada instituição, sem coordenadas, e a sede muitas vezes fica
-- fora da região (ex.: UNIP em São Paulo). O mapa precisa do ponto de
-- cada campus. Os locais foram levantados em fontes oficiais (INEP,
-- sites das instituições) e as coordenadas no OpenStreetMap, num
-- arquivo versionado: backend/data/referencia/ies_locais_oferta.csv.
-- Decisão registrada em docs/decisoes (DEC: coordenadas das IES).
-- ============================================================


-- ------------------------------------------------------------
-- Locais de oferta presencial das IES
-- Uma linha por campus. Uma IES pode ter mais de um campus no
-- mesmo município (ex.: CEUNSP em Itu).
-- ------------------------------------------------------------
CREATE TABLE IES_LOCAL_OFERTA (
    ID_LOCAL              BIGINT GENERATED ALWAYS AS IDENTITY,
    CO_IES                INTEGER        NOT NULL,
    CD_MUN                CHAR(7)        NOT NULL,
    NO_LOCAL              VARCHAR(200)   NOT NULL,
    DS_ENDERECO           VARCHAR(350),
    NO_BAIRRO             VARCHAR(150),
    NU_CEP                CHAR(8),
    VL_LATITUDE           NUMERIC(10,7)  NOT NULL,
    VL_LONGITUDE          NUMERIC(10,7)  NOT NULL,
    GEOMETRY              GEOMETRY(Point, 4674) NOT NULL,
    DS_PRECISAO           VARCHAR(20)    NOT NULL,
    DS_FONTE_ENDERECO     VARCHAR(200)   NOT NULL,
    DS_FONTE_COORDENADA   VARCHAR(200)   NOT NULL,
    DS_OBSERVACAO         TEXT,
    ID_INGESTAO           BIGINT
);

ALTER TABLE IES_LOCAL_OFERTA
    ADD CONSTRAINT PK_IES_LOCAL_OFERTA PRIMARY KEY (ID_LOCAL),
    ADD CONSTRAINT UQ_IES_LOCAL_OFERTA UNIQUE (CO_IES, CD_MUN, NO_LOCAL),
    ADD CONSTRAINT FK_IES_LOCAL_OFERTA_MUNICIPIO
        FOREIGN KEY (CD_MUN) REFERENCES IBGE_MUNICIPIOS (CD_MUN),
    ADD CONSTRAINT FK_IES_LOCAL_OFERTA_INGESTAO
        FOREIGN KEY (ID_INGESTAO) REFERENCES CONTROLE_INGESTAO (ID_INGESTAO),
    -- edificio = ponto no prédio; numero = no número do endereço;
    -- rua = na rua certa, sem o número (pode estar a algumas quadras).
    ADD CONSTRAINT CK_IES_LOCAL_OFERTA_PRECISAO
        CHECK (DS_PRECISAO IN ('edificio', 'numero', 'rua')),
    ADD CONSTRAINT CK_IES_LOCAL_OFERTA_LATITUDE
        CHECK (VL_LATITUDE BETWEEN -90 AND 90),
    ADD CONSTRAINT CK_IES_LOCAL_OFERTA_LONGITUDE
        CHECK (VL_LONGITUDE BETWEEN -180 AND 180);

CREATE INDEX IDX_IES_LOCAL_OFERTA_GEOMETRY ON IES_LOCAL_OFERTA USING GIST (GEOMETRY);
CREATE INDEX IDX_IES_LOCAL_OFERTA_IES_MUN ON IES_LOCAL_OFERTA (CO_IES, CD_MUN);

ALTER TABLE IES_LOCAL_OFERTA ENABLE ROW LEVEL SECURITY;


-- ------------------------------------------------------------
-- Faculdades no mapa: um ponto por campus, com a IES e os cursos
-- presenciais do município. Usa a edição mais recente do Censo Superior.
-- ------------------------------------------------------------
CREATE VIEW VW_FACULDADES_MAPA WITH (security_invoker = true) AS
WITH ano AS (
    SELECT MAX(NU_ANO_CENSO) AS NU_ANO_CENSO FROM MEC_CURSOS
),
cursos AS (
    SELECT c.NU_ANO_CENSO, c.CO_IES, c.CO_MUNICIPIO,
           COUNT(*) AS QT_CURSOS_PRESENCIAIS,
           COALESCE(SUM(c.QT_MAT), 0) AS QT_MATRICULAS,
           JSON_AGG(JSON_BUILD_OBJECT(
               'codigo', c.CO_CURSO,
               'nome', c.NO_CURSO,
               'grau', CASE c.TP_GRAU_ACADEMICO WHEN 1 THEN 'Bacharelado'
                           WHEN 2 THEN 'Licenciatura' WHEN 3 THEN 'Tecnológico'
                           WHEN 4 THEN 'Bacharelado e Licenciatura' END,
               'area', c.NO_CINE_AREA_GERAL,
               'gratuito', c.IN_GRATUITO,
               'vagas', c.QT_VG_TOTAL,
               'matriculas', c.QT_MAT
           ) ORDER BY c.NO_CURSO) AS JS_CURSOS
    FROM MEC_CURSOS c
    JOIN ano a ON a.NU_ANO_CENSO = c.NU_ANO_CENSO
    WHERE c.TP_DIMENSAO = 1
    GROUP BY c.NU_ANO_CENSO, c.CO_IES, c.CO_MUNICIPIO
)
SELECT
    l.ID_LOCAL,
    cu.NU_ANO_CENSO,
    l.CO_IES,
    i.NO_IES,
    i.SG_IES,
    l.NO_LOCAL,
    CASE i.TP_REDE WHEN 1 THEN 'Pública' WHEN 2 THEN 'Privada' END AS DS_REDE,
    CASE i.TP_ORGANIZACAO_ACADEMICA WHEN 1 THEN 'Universidade' WHEN 2 THEN 'Centro Universitário'
         WHEN 3 THEN 'Faculdade' WHEN 4 THEN 'Instituto Federal'
         WHEN 5 THEN 'Centro Federal de Educação Tecnológica' END AS DS_ORGANIZACAO_ACADEMICA,
    -- Fatecs (Centro Paula Souza): todas têm "FATEC" na sigla ou no nome.
    -- Não usar "Faculdade de Tecnologia": SENAI e FAMO também se chamam assim.
    (UPPER(COALESCE(i.SG_IES, '') || ' ' || i.NO_IES) LIKE '%FATEC%') AS E_FATEC,
    l.CD_MUN,
    m.NM_MUN AS NO_MUNICIPIO,
    l.DS_ENDERECO,
    l.NO_BAIRRO,
    l.NU_CEP,
    cu.QT_CURSOS_PRESENCIAIS,
    cu.QT_MATRICULAS,
    cu.JS_CURSOS,
    l.DS_PRECISAO AS DS_PRECISAO_LOCALIZACAO,
    l.DS_FONTE_ENDERECO,
    l.DS_FONTE_COORDENADA,
    ST_Intersects(m.GEOMETRY, l.GEOMETRY) AS PONTO_CONFERE_MUNICIPIO,
    ST_Y(ST_Transform(l.GEOMETRY, 4326)) AS LATITUDE,
    ST_X(ST_Transform(l.GEOMETRY, 4326)) AS LONGITUDE,
    ST_Transform(l.GEOMETRY, 4326) AS GEOMETRIA
FROM IES_LOCAL_OFERTA l
JOIN IBGE_MUNICIPIOS m ON m.CD_MUN = l.CD_MUN
JOIN cursos cu ON cu.CO_IES = l.CO_IES AND cu.CO_MUNICIPIO = l.CD_MUN
JOIN MEC_IES i ON i.NU_ANO_CENSO = cu.NU_ANO_CENSO AND i.CO_IES = l.CO_IES;


-- ------------------------------------------------------------
-- Ofertas presenciais (IES x município) que ainda não têm local
-- com coordenada. Deve ficar vazia; serve para a verificação do banco.
-- ------------------------------------------------------------
CREATE VIEW VW_FACULDADES_SEM_LOCAL WITH (security_invoker = true) AS
SELECT DISTINCT v.NU_ANO_CENSO, v.CO_IES, v.NO_IES, v.SG_IES, v.CO_MUNICIPIO, v.NO_MUNICIPIO
FROM VW_CURSOS_SUPERIORES v
WHERE v.E_PRESENCIAL
  AND v.NU_ANO_CENSO = (SELECT MAX(NU_ANO_CENSO) FROM MEC_CURSOS)
  AND NOT EXISTS (
      SELECT 1 FROM IES_LOCAL_OFERTA l
      WHERE l.CO_IES = v.CO_IES AND l.CD_MUN = v.CO_MUNICIPIO
  );

-- ============================================================
-- FIM DA MIGRATION 004
-- ============================================================
