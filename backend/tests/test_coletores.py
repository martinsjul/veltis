"""Testes das regras de cada coletor, com amostras pequenas no formato oficial.

Não acessam banco nem internet: testam só transformação e validação.
"""

import pandas as pd
import pytest

from src.collectors import censo_escolar, censo_superior, localizacao_escolas, sidra
from src.validators.basicos import ErroValidacao


SOROCABA = "3552205"
CAMPINAS = "3509502"  # fora da RMS


# ------------------------------------------------------------
# Censo Escolar - escolas
# ------------------------------------------------------------

def linha_escola(**alteracoes):
    base = {
        "NU_ANO_CENSO": "2025", "CO_ENTIDADE": "35000001", "NO_ENTIDADE": "ESCOLA A",
        "CO_MUNICIPIO": SOROCABA, "NO_MUNICIPIO": "Sorocaba", "SG_UF": "SP",
        "TP_DEPENDENCIA": "2", "TP_LOCALIZACAO": "1", "TP_SITUACAO_FUNCIONAMENTO": "1",
        "IN_COMUM_MEDIO_MEDIO": "1", "IN_COMUM_MEDIO_INTEGRADO": "0",
        "IN_COMUM_MEDIO_FIC": "0", "IN_COMUM_MEDIO_NORMAL": "0",
        "IN_ITINERARIO_TECN_PROF": "0",
    }
    base.update(alteracoes)
    return base


def test_escolas_filtra_rms_e_converte_tipos():
    df = pd.DataFrame([
        linha_escola(),
        linha_escola(CO_ENTIDADE="35000002", CO_MUNICIPIO=CAMPINAS),
        # paralisada: indicadores vazios = "não se aplica"
        linha_escola(CO_ENTIDADE="35000003", TP_SITUACAO_FUNCIONAMENTO="2",
                     IN_COMUM_MEDIO_MEDIO="", IN_COMUM_MEDIO_INTEGRADO="",
                     IN_COMUM_MEDIO_FIC="", IN_COMUM_MEDIO_NORMAL="",
                     IN_ITINERARIO_TECN_PROF=""),
    ])

    saida = censo_escolar.processar_escolas(df, 2025)

    assert saida["co_entidade"].tolist() == [35000001, 35000003]
    assert saida.iloc[0]["in_comum_medio_medio"] is True
    assert saida.iloc[1]["in_comum_medio_medio"] is None


def test_escolas_recusa_duplicidade():
    df = pd.DataFrame([linha_escola(), linha_escola()])
    with pytest.raises(ErroValidacao, match="duplicadas"):
        censo_escolar.processar_escolas(df, 2025)


def test_escolas_recusa_ano_diferente_da_edicao():
    with pytest.raises(ErroValidacao, match="domínio"):
        censo_escolar.processar_escolas(pd.DataFrame([linha_escola()]), 2024)


def test_escolas_recusa_dependencia_invalida():
    with pytest.raises(ErroValidacao, match="domínio"):
        censo_escolar.processar_escolas(pd.DataFrame([linha_escola(TP_DEPENDENCIA="9")]), 2025)


def test_escolas_recusa_arquivo_sem_coluna():
    df = pd.DataFrame([linha_escola()]).drop(columns="TP_LOCALIZACAO")
    with pytest.raises(ErroValidacao, match="mudou de estrutura"):
        censo_escolar.processar_escolas(df, 2025)


# ------------------------------------------------------------
# Censo Escolar - cursos técnicos
# ------------------------------------------------------------

def linha_curso_tecnico(**alteracoes):
    base = {
        "NU_ANO_CENSO": "2025", "CO_ENTIDADE": "35000001", "CO_MUNICIPIO": SOROCABA,
        "NO_MUNICIPIO": "Sorocaba", "CO_CURSO_EDUC_PROFISSIONAL": "3041",
        "NO_CURSO_EDUC_PROFISSIONAL": "Manutenção Automotiva",
        "ID_AREA_CURSO_PROFISSIONAL": "3000",
        "NO_AREA_CURSO_PROFISSIONAL": "Controle e processos industriais",
        "QT_CURSO_TEC": "1", "QT_MAT_CURSO_TEC": "34",
    }
    base.update(alteracoes)
    return base


def test_cursos_tecnicos_exige_escola_carregada():
    df = pd.DataFrame([linha_curso_tecnico()])

    saida = censo_escolar.processar_cursos_tecnicos(df, 2025, escolas_no_banco={35000001})
    assert saida.iloc[0]["qt_mat_curso_tec"] == 34

    with pytest.raises(ErroValidacao, match="não estão em INEP_ESCOLA"):
        censo_escolar.processar_cursos_tecnicos(df, 2025, escolas_no_banco=set())


# ------------------------------------------------------------
# Censo Superior
# ------------------------------------------------------------

def linha_curso_superior(**alteracoes):
    base = {
        "NU_ANO_CENSO": "2024", "TP_DIMENSAO": "1", "CO_IES": "33", "CO_CURSO": "1001",
        "NO_CURSO": "Análise e Desenvolvimento de Sistemas", "CO_MUNICIPIO": SOROCABA,
        "NO_MUNICIPIO": "Sorocaba", "SG_UF": "SP", "NO_CINE_AREA_GERAL": "Computação",
        "NO_CINE_AREA_ESPECIFICA": "Computação", "TP_GRAU_ACADEMICO": "3",
        "IN_GRATUITO": "1", "TP_MODALIDADE_ENSINO": "1", "TP_NIVEL_ACADEMICO": "1",
        "QT_CURSO": "1", "QT_VG_TOTAL": "40", "QT_MAT": "120",
    }
    base.update(alteracoes)
    return base


def test_cursos_superiores_mantem_so_dimensoes_1_e_2_na_rms():
    df = pd.DataFrame([
        linha_curso_superior(),
        linha_curso_superior(CO_CURSO="1002", TP_DIMENSAO="2", TP_MODALIDADE_ENSINO="2",
                             QT_CURSO="0", QT_VG_TOTAL="0", QT_MAT="15"),
        linha_curso_superior(CO_CURSO="1003", TP_DIMENSAO="3", CO_MUNICIPIO=""),
        linha_curso_superior(CO_CURSO="1004", CO_MUNICIPIO=CAMPINAS),
    ])

    saida = censo_superior.processar_cursos(df, 2024)

    assert saida["co_curso"].tolist() == [1001, 1002]
    assert saida["in_gratuito"].tolist() == [True, True]


def test_cursos_superiores_recusa_oferta_duplicada():
    df = pd.DataFrame([linha_curso_superior(), linha_curso_superior()])
    with pytest.raises(ErroValidacao, match="duplicadas"):
        censo_superior.processar_cursos(df, 2024)


def test_ies_carrega_as_que_ofertam_mesmo_com_sede_fora():
    df = pd.DataFrame([
        {
            "NU_ANO_CENSO": "2024", "CO_IES": "1", "NO_IES": "UNIVERSIDADE X", "SG_IES": "",
            "CO_MUNICIPIO_IES": "3550308", "NO_MUNICIPIO_IES": "São Paulo", "SG_UF_IES": "SP",
            "TP_ORGANIZACAO_ACADEMICA": "1", "TP_REDE": "2", "TP_CATEGORIA_ADMINISTRATIVA": "4",
            "DS_ENDERECO_IES": "Rua A", "DS_NUMERO_ENDERECO_IES": "10",
            "DS_COMPLEMENTO_ENDERECO_IES": "-", "NO_BAIRRO_IES": "Centro",
            "NU_CEP_IES": "1310100",
        },
        {
            "NU_ANO_CENSO": "2024", "CO_IES": "2", "NO_IES": "SEM OFERTA", "SG_IES": "",
            "CO_MUNICIPIO_IES": SOROCABA, "NO_MUNICIPIO_IES": "Sorocaba", "SG_UF_IES": "SP",
            "TP_ORGANIZACAO_ACADEMICA": "3", "TP_REDE": "2", "TP_CATEGORIA_ADMINISTRATIVA": "4",
            "DS_ENDERECO_IES": "", "DS_NUMERO_ENDERECO_IES": "",
            "DS_COMPLEMENTO_ENDERECO_IES": "", "NO_BAIRRO_IES": "", "NU_CEP_IES": "",
        },
    ])

    saida = censo_superior.processar_ies(df, 2024, ies_com_oferta={1})

    assert saida["co_ies"].tolist() == [1]
    assert saida.iloc[0]["ds_endereco_ies"] == "Rua A, 10"   # "-" não entra
    assert saida.iloc[0]["nu_cep_ies"] == "01310100"
    assert saida.iloc[0]["sg_ies"] is None

    with pytest.raises(ErroValidacao, match="não estão no arquivo de IES"):
        censo_superior.processar_ies(df, 2024, ies_com_oferta={1, 999})


# ------------------------------------------------------------
# Localização das escolas
# ------------------------------------------------------------

def test_localizacao_reconhece_colunas_com_acento_e_maiusculas():
    df = pd.DataFrame(columns=["Escola", "Código INEP", "Endereço", "Latitude", "Longitude"])
    config = localizacao_escolas.FONTES_LOCALIZACAO[0]
    mapa = localizacao_escolas.mapear_colunas(df, config["colunas"], "Catálogo")
    assert mapa["codigo"] == "Código INEP"
    assert mapa["latitude"] == "Latitude"


def test_localizacao_sem_coluna_de_codigo_explica_o_problema():
    df = pd.DataFrame(columns=["Escola", "Latitude", "Longitude"])
    config = localizacao_escolas.FONTES_LOCALIZACAO[0]
    with pytest.raises(ErroValidacao, match="código INEP"):
        localizacao_escolas.mapear_colunas(df, config["colunas"], "Catálogo")


def test_localizacao_regras_de_coordenada_e_universo():
    df = pd.DataFrame(
        {
            "Código INEP": ["1", "2", "3", "4", "999"],
            "Endereço": ["RUA A, 1. 18035-000 Sorocaba", "RUA B", "", "RUA D", "RUA X"],
            "Latitude": ["-23,50", "0", "", "", "-23,5"],
            "Longitude": ["-47,45", "0", "", "", "-47,4"],
        }
    )
    config = localizacao_escolas.FONTES_LOCALIZACAO[0]
    mapa = localizacao_escolas.mapear_colunas(df, config["colunas"], "Catálogo")

    saida, resumo = localizacao_escolas.processar_localizacoes(
        df, mapa, escolas_validas={1, 2, 3, 4}, ano=2025, origem="Catálogo"
    )

    por_escola = saida.set_index("co_entidade")
    # 1: ponto válido; CEP extraído do texto do endereço
    assert por_escola.loc[1, "tp_metodo_localizacao"] == "COORDENADA_OFICIAL"
    assert por_escola.loc[1, "geometry"] == "POINT(-47.45 -23.5)"
    assert por_escola.loc[1, "nu_cep"] == "18035000"
    # 2: coordenada (0,0) é descartada, mas o endereço fica
    assert por_escola.loc[2, "tp_metodo_localizacao"] == "ENDERECO_OFICIAL"
    assert por_escola.loc[2, "geometry"] is None
    # 3: sem endereço nem ponto -> não é gravada
    assert 3 not in por_escola.index
    assert resumo == {
        "linhas_arquivo": 5,
        "fora_do_universo": 1,        # código 999 não é escola do Censo/RMS
        "gravadas": 3,
        "com_coordenada": 1,
        "coordenadas_descartadas": 1,
        "sem_endereco_nem_ponto": 1,
    }


# ------------------------------------------------------------
# SIDRA
# ------------------------------------------------------------

def resposta_sidra(codigos):
    """Resposta no formato real da API v3 (tabela sem classificações)."""

    return [
        {
            "id": "93",
            "variavel": "População residente",
            "unidade": "Pessoas",
            "resultados": [
                {
                    "classificacoes": [],
                    "series": [
                        {"localidade": {"id": c, "nivel": {"id": "N6"}, "nome": "X"},
                         "serie": {"2022": "100"}}
                        for c in codigos
                    ],
                }
            ],
        }
    ]


INDICADOR_4709 = {
    "agregado": "4709", "periodos": ["2022"], "variaveis": ["93"],
    "classificacoes": {}, "descricao": "teste",
}


def test_sidra_transforma_e_valida_27_municipios():
    from src.config.rms import CODIGOS_RMS

    df = sidra.transformar(resposta_sidra(CODIGOS_RMS), INDICADOR_4709)
    sidra.validar_indicador(df, INDICADOR_4709)

    assert len(df) == 27
    assert set(df["ds_chave_classificacao"]) == {""}


def test_sidra_recusa_resposta_incompleta():
    from src.config.rms import CODIGOS_RMS

    df = sidra.transformar(resposta_sidra(CODIGOS_RMS[:26]), INDICADOR_4709)
    with pytest.raises(ErroValidacao, match="esperados 27"):
        sidra.validar_indicador(df, INDICADOR_4709)


def test_sidra_consulta_pede_categorias_explicitas():
    indicador = {
        "agregado": "9514", "periodos": ["2022"], "variaveis": ["93"],
        "classificacoes": {"2": ["6794", "4", "5"], "287": ["100362", "93070"]},
        "descricao": "teste",
    }
    _, parametros = sidra.montar_consulta(indicador)

    assert parametros["classificacao"] == "2[6794,4,5]|287[100362,93070]"
    assert sidra.valores_esperados(indicador) == 27 * 3 * 2
