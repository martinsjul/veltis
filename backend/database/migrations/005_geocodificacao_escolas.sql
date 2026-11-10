-- ============================================================
-- VELTIS - MIGRATION 005
-- Coordenadas geocodificadas para as escolas sem ponto oficial.
--
-- Por quê: parte das escolas não tem coordenada no Catálogo do INEP
-- nem na SEDUC-SP, mas tem endereço. O pipeline "geocodificacao"
-- calcula o ponto a partir do endereço com o geocodebr (Ipea), que usa
-- o CNEFE do IBGE (Censo 2022). Esses pontos entram em
-- ESCOLA_LOCALIZACAO como mais uma fonte, com TP_METODO_LOCALIZACAO =
-- 'GEOCODIFICADO', e nunca substituem uma coordenada oficial.
-- Decisão: docs/decisoes/DEC-002-geocodificacao-das-escolas.md
-- ============================================================


-- ------------------------------------------------------------
-- Precisão do ponto (só para pontos geocodificados)
--   numero / numero_aproximado: no número do endereço (ou vizinho)
--   logradouro: na rua certa, sem o número
--   cep / localidade / municipio: mais grosseiro (o pipeline não grava)
-- VL_DESVIO_METROS: raio em que estão 95% dos endereços do CNEFE que
-- casaram com o endereço da escola (quanto menor, mais confiável).
-- ------------------------------------------------------------
ALTER TABLE ESCOLA_LOCALIZACAO
    ADD COLUMN DS_PRECISAO      VARCHAR(20),
    ADD COLUMN VL_DESVIO_METROS INTEGER;

ALTER TABLE ESCOLA_LOCALIZACAO
    ADD CONSTRAINT CK_ESCOLA_LOCALIZACAO_PRECISAO
        CHECK (DS_PRECISAO IS NULL OR DS_PRECISAO IN (
            'numero', 'numero_aproximado', 'logradouro', 'cep', 'localidade', 'municipio'
        )),
    ADD CONSTRAINT CK_ESCOLA_LOCALIZACAO_DESVIO
        CHECK (VL_DESVIO_METROS IS NULL OR VL_DESVIO_METROS >= 0);


-- ------------------------------------------------------------
-- Escolas para o mapa: agora o PONTO e o ENDEREÇO podem vir de fontes
-- diferentes.
--   Ponto:    coordenada oficial primeiro (Catálogo INEP, depois SEDUC);
--             geocodificado só quando não há nenhuma oficial.
--   Endereço: Catálogo INEP primeiro, depois SEDUC (fontes oficiais).
-- As colunas antigas continuam iguais; duas novas entram no fim.
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW VW_ESCOLAS_MAPA WITH (security_invoker = true) AS
WITH locais AS (
    SELECT l.*, f.NO_ORGAO, f.NO_ORGAO || ' - ' || f.NO_FONTE AS FONTE_LOCALIZACAO
    FROM ESCOLA_LOCALIZACAO l
    JOIN FONTE_DADOS f ON f.ID_FONTE = l.ID_FONTE
),
melhor_ponto AS (
    SELECT DISTINCT ON (NU_ANO_CENSO, CO_ENTIDADE)
        NU_ANO_CENSO, CO_ENTIDADE, GEOMETRY, TP_METODO_LOCALIZACAO,
        FONTE_LOCALIZACAO, DS_PRECISAO, VL_DESVIO_METROS
    FROM locais
    WHERE GEOMETRY IS NOT NULL
    ORDER BY NU_ANO_CENSO, CO_ENTIDADE,
             (TP_METODO_LOCALIZACAO = 'COORDENADA_OFICIAL') DESC,
             (NO_ORGAO = 'INEP') DESC,
             VL_DESVIO_METROS NULLS FIRST
),
melhor_endereco AS (
    SELECT DISTINCT ON (NU_ANO_CENSO, CO_ENTIDADE)
        NU_ANO_CENSO, CO_ENTIDADE, DS_ENDERECO, NU_CEP, NU_TELEFONE,
        TP_METODO_LOCALIZACAO, FONTE_LOCALIZACAO
    FROM locais
    WHERE TP_METODO_LOCALIZACAO <> 'GEOCODIFICADO'
    ORDER BY NU_ANO_CENSO, CO_ENTIDADE,
             (DS_ENDERECO IS NULL),
             (NO_ORGAO = 'INEP') DESC
),
tecnicos AS (
    SELECT NU_ANO_CENSO, CO_ENTIDADE,
           COUNT(*) FILTER (WHERE ID_AREA_CURSO_PROFISSIONAL <> 999) AS QT_CURSOS_TECNICOS,
           SUM(QT_MAT_CURSO_TEC) AS QT_MATRICULAS_EDUC_PROFISSIONAL
    FROM INEP_CURSO_TECNICO
    GROUP BY NU_ANO_CENSO, CO_ENTIDADE
)
SELECT
    e.NU_ANO_CENSO,
    e.CO_ENTIDADE,
    e.NO_ENTIDADE,
    e.CO_MUNICIPIO,
    e.NO_MUNICIPIO,
    e.TP_DEPENDENCIA,
    CASE e.TP_DEPENDENCIA WHEN 1 THEN 'Federal' WHEN 2 THEN 'Estadual'
                          WHEN 3 THEN 'Municipal' WHEN 4 THEN 'Privada' END AS DS_DEPENDENCIA,
    CASE e.TP_LOCALIZACAO WHEN 1 THEN 'Urbana' WHEN 2 THEN 'Rural' END AS DS_LOCALIZACAO,
    CASE e.TP_SITUACAO_FUNCIONAMENTO WHEN 1 THEN 'Em atividade' WHEN 2 THEN 'Paralisada'
         WHEN 3 THEN 'Extinta no ano' WHEN 4 THEN 'Extinta em anos anteriores' END AS DS_SITUACAO,
    (e.TP_SITUACAO_FUNCIONAMENTO = 1) AS EM_ATIVIDADE,
    e.IN_COMUM_MEDIO_MEDIO AS OFERECE_ENSINO_MEDIO,
    e.IN_COMUM_MEDIO_INTEGRADO AS OFERECE_MEDIO_INTEGRADO,
    e.IN_COMUM_MEDIO_NORMAL AS OFERECE_NORMAL_MAGISTERIO,
    e.IN_ITINERARIO_TECN_PROF AS OFERECE_ITINERARIO_TECNICO,
    COALESCE(t.QT_CURSOS_TECNICOS, 0) AS QT_CURSOS_TECNICOS,
    COALESCE(t.QT_MATRICULAS_EDUC_PROFISSIONAL, 0) AS QT_MATRICULAS_EDUC_PROFISSIONAL,
    me.DS_ENDERECO,
    me.NU_CEP,
    me.NU_TELEFONE,
    COALESCE(mp.TP_METODO_LOCALIZACAO, me.TP_METODO_LOCALIZACAO) AS TP_METODO_LOCALIZACAO,
    COALESCE(mp.FONTE_LOCALIZACAO, me.FONTE_LOCALIZACAO) AS FONTE_LOCALIZACAO,
    (mp.GEOMETRY IS NOT NULL) AS TEM_COORDENADA,
    CASE WHEN mp.GEOMETRY IS NULL THEN NULL
         ELSE ST_Intersects(m.GEOMETRY, mp.GEOMETRY) END AS PONTO_CONFERE_MUNICIPIO,
    ST_Y(ST_Transform(mp.GEOMETRY, 4326)) AS LATITUDE,
    ST_X(ST_Transform(mp.GEOMETRY, 4326)) AS LONGITUDE,
    ST_Transform(mp.GEOMETRY, 4326) AS GEOMETRIA,
    -- novas
    CASE WHEN mp.GEOMETRY IS NULL THEN NULL
         WHEN mp.TP_METODO_LOCALIZACAO = 'GEOCODIFICADO' THEN mp.DS_PRECISAO
         ELSE 'oficial' END AS DS_PRECISAO_LOCALIZACAO,
    mp.VL_DESVIO_METROS
FROM INEP_ESCOLA e
JOIN IBGE_MUNICIPIOS m ON m.CD_MUN = e.CO_MUNICIPIO
LEFT JOIN melhor_ponto mp ON mp.NU_ANO_CENSO = e.NU_ANO_CENSO AND mp.CO_ENTIDADE = e.CO_ENTIDADE
LEFT JOIN melhor_endereco me ON me.NU_ANO_CENSO = e.NU_ANO_CENSO AND me.CO_ENTIDADE = e.CO_ENTIDADE
LEFT JOIN tecnicos t ON t.NU_ANO_CENSO = e.NU_ANO_CENSO AND t.CO_ENTIDADE = e.CO_ENTIDADE;

-- ============================================================
-- FIM DA MIGRATION 005
-- ============================================================
