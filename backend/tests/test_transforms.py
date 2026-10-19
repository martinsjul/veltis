"""Testes das conversões reutilizáveis (não precisam de banco nem internet)."""

from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from src.loaders.carga import para_registros
from src.transforms import codigos as conv
from src.transforms.sidra import chave_classificacao, classificacoes_json, converter_valor


def test_codigo_municipio_normaliza_7_digitos():
    serie = pd.Series([3552205, "3552205.0", " 3552205 ", "355220"])
    assert conv.codigo_municipio(serie).tolist() == ["3552205", "3552205", "3552205", "0355220"]


def test_para_booleano_aceita_texto_e_numero_e_vazio_vira_none():
    serie = pd.Series(["0", "1", 1, 0.0, "", None, np.nan])
    assert conv.para_booleano(serie).tolist() == [False, True, True, False, None, None, None]


def test_para_booleano_recusa_valor_estranho():
    with pytest.raises(ValueError):
        conv.para_booleano(pd.Series(["2"]))


def test_para_inteiro_com_vazio():
    resultado = conv.para_inteiro(pd.Series(["10", "", "3"]))
    assert resultado.tolist()[0] == 10
    assert pd.isna(resultado.tolist()[1])


def test_para_texto_remove_aspas_do_inep_e_corta():
    serie = pd.Series(['"0917P01"', "  abc  ", "", "x" * 10])
    assert conv.para_texto(serie, 5).tolist() == ["0917P", "abc", None, "xxxxx"]


@pytest.mark.parametrize(
    "valor, esperado",
    [("-23,5017", -23.5017), ("-47.45", -47.45), ("", None), ("abc", None), (None, None)],
)
def test_para_coordenada(valor, esperado):
    assert conv.para_coordenada(valor) == esperado


@pytest.mark.parametrize(
    "valor, esperado",
    [("18.035-000", "18035000"), (1035000, "01035000"), (18035000.0, "18035000"), ("", None)],
)
def test_somente_digitos_cep(valor, esperado):
    assert conv.somente_digitos(valor, 8) == esperado


def test_normalizar_nome_de_coluna():
    assert conv.normalizar_nome("Código INEP ") == "codigo_inep"
    assert conv.normalizar_nome("DS_LATITUDE") == "ds_latitude"


def test_para_registros_troca_nan_por_none_em_colunas_numericas():
    # No pandas 3, df.where(notnull, None) mantinha NaN em colunas float.
    df = pd.DataFrame({"a": [1.0, np.nan], "b": ["x", None], "c": pd.array([1, None], dtype="Int64")})
    registros = para_registros(df)
    assert registros[1] == {"a": None, "b": None, "c": None}
    assert registros[0]["a"] == 1.0


# ------------------------------------------------------------
# SIDRA
# ------------------------------------------------------------

CLASSIF_IDADE_SEXO = [
    {"id": "287", "nome": "Idade", "categoria": {"93070": "0 a 4 anos"}},
    {"id": "2", "nome": "Sexo", "categoria": {"4": "Homens"}},
    {"id": "286", "nome": "Forma de declaração da idade", "categoria": {"113635": "Total"}},
]


def test_chave_classificacao_independe_da_ordem():
    assert chave_classificacao(CLASSIF_IDADE_SEXO) == "2:4|286:113635|287:93070"
    assert chave_classificacao(list(reversed(CLASSIF_IDADE_SEXO))) == "2:4|286:113635|287:93070"


def test_chave_classificacao_vazia_quando_nao_ha_classificacao():
    assert chave_classificacao([]) == ""


def test_classificacoes_json():
    primeiro = classificacoes_json(CLASSIF_IDADE_SEXO)[0]
    assert primeiro == {
        "cd_classificacao": "2",
        "no_classificacao": "Sexo",
        "cd_categoria": "4",
        "no_categoria": "Homens",
    }


@pytest.mark.parametrize(
    "bruto, unidade, esperado",
    [
        ("723682", "Pessoas", (Decimal("723682"), None)),
        ("1.76", "%", (Decimal("1.76"), None)),
        ("-", "Pessoas", (Decimal(0), "-")),   # zero absoluto em contagem
        ("-", "%", (None, "-")),               # taxa não calculável
        ("X", "Pessoas", (None, "X")),
        ("...", "Pessoas", (None, "...")),
    ],
)
def test_converter_valor_sidra(bruto, unidade, esperado):
    assert converter_valor(bruto, unidade) == esperado


def test_converter_valor_sidra_recusa_texto_desconhecido():
    with pytest.raises(ValueError):
        converter_valor("abc", "Pessoas")
