-- ============================================================
-- VELTIS - MIGRATION 003
-- Views de leitura para a API (FastAPI) e o mapa (React + Leaflet)
--
-- - Geometrias convertidas para WGS 84 (EPSG:4326), que o Leaflet usa.
-- - Códigos traduzidos para texto (dependência, situação, modalidade...).
-- - security_invoker = true: a view respeita o RLS das tabelas, então
--   continua fechada para a API automática do Supabase (chave anon).
-- ============================================================


-- ------------------------------------------------------------
-- Municípios (contorno + população)
-- ------------------------------------------------------------
CREATE VIEW VW_MUNICIPIOS_MAPA WITH (security_invoker = true) AS
SELECT
    m.CD_MUN,
    m.NM_MUN,
    m.AREA_KM2,
    pop.VL_INDICADOR::BIGINT AS POPULACAO_2022,
    ST_Transform(m.GEOMETRY, 4326) AS GEOMETRIA
FROM IBGE_MUNICIPIOS m
LEFT JOIN IBGE_DEMOGRAFICO pop
       ON pop.CD_MUN = m.CD_MUN
      AND pop.CD_AGREGADO = '4709'
      AND pop.CD_VARIAVEL = '93'
      AND pop.CO_PERIODO = '2022'
      AND pop.DS_CHAVE_CLASSIFICACAO = '';


-- ------------------------------------------------------------
-- Indicadores por município (uma linha por município)
-- Taxas vêm prontas do IBGE; nunca some taxas entre municípios.
-- ------------------------------------------------------------
CREATE VIEW VW_INDICADORES_MUNICIPIO WITH (security_invoker = true) AS
WITH d AS (
    SELECT CD_MUN, CD_AGREGADO, CD_VARIAVEL, CO_PERIODO,
           DS_CHAVE_CLASSIFICACAO, JS_CLASSIFICACOES, VL_INDICADOR
    FROM IBGE_DEMOGRAFICO
)
SELECT
    m.CD_MUN,
    m.NM_MUN,

    -- Censo 2022 (tabela 4709) e estimativas (tabela 6579)
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '4709' AND d.CD_VARIAVEL = '93')::BIGINT
        AS POPULACAO_2022,
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '4709' AND d.CD_VARIAVEL = '10605')
        AS TAXA_CRESCIMENTO_2010_2022_PCT,
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '6579' AND d.CO_PERIODO = '2026')::BIGINT
        AS POPULACAO_ESTIMADA_2026,

    -- Área e densidade (tabela 4714)
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '4714' AND d.CD_VARIAVEL = '6318')
        AS AREA_KM2,
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '4714' AND d.CD_VARIAVEL = '614')
        AS DENSIDADE_HAB_KM2,

    -- Sexo e idade (tabela 9514; idade = grupos de 5 anos)
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '9514'
        AND d.DS_CHAVE_CLASSIFICACAO = '2:4|286:113635|287:100362')::BIGINT AS HOMENS,
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '9514'
        AND d.DS_CHAVE_CLASSIFICACAO = '2:5|286:113635|287:100362')::BIGINT AS MULHERES,
    SUM(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '9514'
        AND d.DS_CHAVE_CLASSIFICACAO IN (
            '2:6794|286:113635|287:93070',
            '2:6794|286:113635|287:93084',
            '2:6794|286:113635|287:93085'))::BIGINT AS POPULACAO_0_14,
    SUM(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '9514'
        AND d.DS_CHAVE_CLASSIFICACAO IN (
            '2:6794|286:113635|287:93086',
            '2:6794|286:113635|287:93087',
            '2:6794|286:113635|287:93088'))::BIGINT AS POPULACAO_15_29,
    SUM(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '9514'
        AND d.DS_CHAVE_CLASSIFICACAO IN (
            '2:6794|286:113635|287:93095', '2:6794|286:113635|287:93096',
            '2:6794|286:113635|287:93097', '2:6794|286:113635|287:93098',
            '2:6794|286:113635|287:49108', '2:6794|286:113635|287:49109',
            '2:6794|286:113635|287:60040', '2:6794|286:113635|287:60041',
            '2:6794|286:113635|287:6653'))::BIGINT AS POPULACAO_60_MAIS,

    -- Alfabetização (tabela 9542, pessoas de 15 anos ou mais)
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '9542'
        AND d.JS_CLASSIFICACOES @> '[{"cd_classificacao":"59","cd_categoria":"93024"}]')::BIGINT
        AS PESSOAS_15_MAIS,
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '9542'
        AND d.JS_CLASSIFICACOES @> '[{"cd_classificacao":"59","cd_categoria":"1023"}]')::BIGINT
        AS ALFABETIZADOS_15_MAIS,

    -- Taxa bruta de frequência escolar (tabela 10056), em %
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '10056'
        AND d.JS_CLASSIFICACOES @> '[{"cd_classificacao":"58","cd_categoria":"99749"}]')
        AS FREQUENCIA_ESCOLAR_0_3_PCT,
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '10056'
        AND d.JS_CLASSIFICACOES @> '[{"cd_classificacao":"58","cd_categoria":"47813"}]')
        AS FREQUENCIA_ESCOLAR_4_5_PCT,
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '10056'
        AND d.JS_CLASSIFICACOES @> '[{"cd_classificacao":"58","cd_categoria":"31615"}]')
        AS FREQUENCIA_ESCOLAR_6_14_PCT,
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '10056'
        AND d.JS_CLASSIFICACOES @> '[{"cd_classificacao":"58","cd_categoria":"2792"}]')
        AS FREQUENCIA_ESCOLAR_15_17_PCT,
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '10056'
        AND d.JS_CLASSIFICACOES @> '[{"cd_classificacao":"58","cd_categoria":"100052"}]')
        AS FREQUENCIA_ESCOLAR_18_24_PCT,

    -- Nível de instrução (tabela 10061, pessoas de 18 anos ou mais)
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '10061'
        AND d.JS_CLASSIFICACOES @> '[{"cd_classificacao":"1568","cd_categoria":"120704"}]')::BIGINT
        AS PESSOAS_18_MAIS,
    MAX(d.VL_INDICADOR) FILTER (WHERE d.CD_AGREGADO = '10061'
        AND d.JS_CLASSIFICACOES @> '[{"cd_classificacao":"1568","cd_categoria":"99713"}]')::BIGINT
        AS SUPERIOR_COMPLETO_18_MAIS
FROM IBGE_MUNICIPIOS m
LEFT JOIN d ON d.CD_MUN = m.CD_MUN
GROUP BY m.CD_MUN, m.NM_MUN;


-- ------------------------------------------------------------
-- Escolas para o mapa (uma linha por escola; melhor localização)
-- Prioridade do ponto: Catálogo INEP, depois SEDUC-SP.
-- ------------------------------------------------------------
CREATE VIEW VW_ESCOLAS_MAPA WITH (security_invoker = true) AS
WITH melhor_local AS (
    SELECT DISTINCT ON (l.NU_ANO_CENSO, l.CO_ENTIDADE)
        l.NU_ANO_CENSO, l.CO_ENTIDADE, l.DS_ENDERECO, l.NU_CEP, l.NU_TELEFONE,
        l.GEOMETRY, l.TP_METODO_LOCALIZACAO,
        f.NO_ORGAO || ' - ' || f.NO_FONTE AS FONTE_LOCALIZACAO
    FROM ESCOLA_LOCALIZACAO l
    JOIN FONTE_DADOS f ON f.ID_FONTE = l.ID_FONTE
    ORDER BY l.NU_ANO_CENSO, l.CO_ENTIDADE,
             (l.GEOMETRY IS NULL),
             (f.NO_ORGAO = 'INEP') DESC
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
    ml.DS_ENDERECO,
    ml.NU_CEP,
    ml.NU_TELEFONE,
    ml.TP_METODO_LOCALIZACAO,
    ml.FONTE_LOCALIZACAO,
    (ml.GEOMETRY IS NOT NULL) AS TEM_COORDENADA,
    CASE WHEN ml.GEOMETRY IS NULL THEN NULL
         ELSE ST_Intersects(m.GEOMETRY, ml.GEOMETRY) END AS PONTO_CONFERE_MUNICIPIO,
    ST_Y(ST_Transform(ml.GEOMETRY, 4326)) AS LATITUDE,
    ST_X(ST_Transform(ml.GEOMETRY, 4326)) AS LONGITUDE,
    ST_Transform(ml.GEOMETRY, 4326) AS GEOMETRIA
FROM INEP_ESCOLA e
JOIN IBGE_MUNICIPIOS m ON m.CD_MUN = e.CO_MUNICIPIO
LEFT JOIN melhor_local ml ON ml.NU_ANO_CENSO = e.NU_ANO_CENSO AND ml.CO_ENTIDADE = e.CO_ENTIDADE
LEFT JOIN tecnicos t ON t.NU_ANO_CENSO = e.NU_ANO_CENSO AND t.CO_ENTIDADE = e.CO_ENTIDADE;


-- ------------------------------------------------------------
-- Cursos técnicos com a escola
-- ------------------------------------------------------------
CREATE VIEW VW_CURSOS_TECNICOS WITH (security_invoker = true) AS
SELECT
    c.NU_ANO_CENSO,
    c.CO_ENTIDADE,
    e.NO_ENTIDADE,
    CASE e.TP_DEPENDENCIA WHEN 1 THEN 'Federal' WHEN 2 THEN 'Estadual'
                          WHEN 3 THEN 'Municipal' WHEN 4 THEN 'Privada' END AS DS_DEPENDENCIA,
    c.CO_MUNICIPIO,
    c.NO_MUNICIPIO,
    c.CO_CURSO_EDUC_PROFISSIONAL,
    c.NO_CURSO_EDUC_PROFISSIONAL,
    c.ID_AREA_CURSO_PROFISSIONAL,
    c.NO_AREA_CURSO_PROFISSIONAL,
    (c.ID_AREA_CURSO_PROFISSIONAL = 999) AS E_NORMAL_MAGISTERIO,
    c.QT_MAT_CURSO_TEC
FROM INEP_CURSO_TECNICO c
JOIN INEP_ESCOLA e ON e.NU_ANO_CENSO = c.NU_ANO_CENSO AND e.CO_ENTIDADE = c.CO_ENTIDADE;


-- ------------------------------------------------------------
-- Cursos superiores por local de oferta, com a IES
-- ------------------------------------------------------------
CREATE VIEW VW_CURSOS_SUPERIORES WITH (security_invoker = true) AS
SELECT
    c.NU_ANO_CENSO,
    c.CO_MUNICIPIO,
    c.NO_MUNICIPIO,
    c.CO_IES,
    i.NO_IES,
    i.SG_IES,
    CASE i.TP_REDE WHEN 1 THEN 'Pública' WHEN 2 THEN 'Privada' END AS DS_REDE,
    CASE i.TP_ORGANIZACAO_ACADEMICA WHEN 1 THEN 'Universidade' WHEN 2 THEN 'Centro Universitário'
         WHEN 3 THEN 'Faculdade' WHEN 4 THEN 'Instituto Federal'
         WHEN 5 THEN 'Centro Federal de Educação Tecnológica' END AS DS_ORGANIZACAO_ACADEMICA,
    (i.CO_MUNICIPIO_IES = c.CO_MUNICIPIO) AS SEDE_NO_MUNICIPIO,
    c.CO_CURSO,
    c.NO_CURSO,
    c.NO_CINE_AREA_GERAL,
    c.NO_CINE_AREA_ESPECIFICA,
    CASE c.TP_GRAU_ACADEMICO WHEN 1 THEN 'Bacharelado' WHEN 2 THEN 'Licenciatura'
         WHEN 3 THEN 'Tecnológico' WHEN 4 THEN 'Bacharelado e Licenciatura' END AS DS_GRAU_ACADEMICO,
    CASE c.TP_MODALIDADE_ENSINO WHEN 1 THEN 'Presencial' WHEN 2 THEN 'EAD' END AS DS_MODALIDADE,
    (c.TP_DIMENSAO = 1) AS E_PRESENCIAL,
    c.IN_GRATUITO AS E_GRATUITO,
    -- Na oferta EAD por município (dimensão 2) o INEP zera vagas;
    -- use matrículas para essas linhas.
    CASE WHEN c.TP_DIMENSAO = 1 THEN c.QT_VG_TOTAL END AS QT_VAGAS,
    c.QT_MAT AS QT_MATRICULAS,
    (c.QT_MAT > 0) AS COM_MATRICULA
FROM MEC_CURSOS c
JOIN MEC_IES i ON i.NU_ANO_CENSO = c.NU_ANO_CENSO AND i.CO_IES = c.CO_IES;


-- ------------------------------------------------------------
-- Auditoria: última carga de cada fonte/arquivo
-- ------------------------------------------------------------
CREATE VIEW VW_ULTIMAS_CARGAS WITH (security_invoker = true) AS
SELECT DISTINCT ON (c.ID_FONTE, c.NO_ARQUIVO_ORIGEM)
    f.NO_ORGAO,
    f.NO_FONTE,
    c.NO_ARQUIVO_ORIGEM,
    c.CO_PERIODO_REFERENCIA,
    c.DS_STATUS,
    c.DT_PROCESSAMENTO,
    c.QT_REGISTROS_LIDOS,
    c.QT_REGISTROS_CARREGADOS,
    c.QT_REGISTROS_REJEITADOS,
    c.DS_OBSERVACAO
FROM CONTROLE_INGESTAO c
JOIN FONTE_DADOS f ON f.ID_FONTE = c.ID_FONTE
ORDER BY c.ID_FONTE, c.NO_ARQUIVO_ORIGEM, c.DT_PROCESSAMENTO DESC;

-- ============================================================
-- FIM DA MIGRATION 003
-- ============================================================
