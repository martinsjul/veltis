"""Testes do arquivo de locais das faculdades (sem banco)."""

import pandas as pd
import pytest

from src.collectors.locais_ies import ARQUIVO, ler_locais, processar_locais
from src.config.rms import CODIGOS_RMS
from src.validators.basicos import ErroValidacao


def _linha(**mudancas):
    base = {
        "co_ies": "33", "cd_mun": "3552205", "no_local": "Fatec Sorocaba",
        "ds_endereco": "Avenida Engenheiro Carlos Reinaldo Mendes, 2015",
        "no_bairro": "Alto da Boa Vista", "nu_cep": "18013-280",
        "latitude": "-23.480133", "longitude": "-47.425939", "ds_precisao": "edificio",
        "ds_fonte_endereco": "INEP", "ds_fonte_coordenada": "OpenStreetMap",
        "ds_observacao": "",
    }
    return {**base, **mudancas}


def test_arquivo_real_do_repositorio_e_valido():
    locais = processar_locais(ler_locais(ARQUIVO))
    assert len(locais) >= 33
    assert set(locais["cd_mun"]) <= set(CODIGOS_RMS)
    assert locais["vl_latitude"].between(-25.5, -19.5).all()


def test_linha_valida_vira_ponto():
    locais = processar_locais(pd.DataFrame([_linha()]))
    linha = locais.iloc[0]
    assert linha["co_ies"] == 33
    assert linha["nu_cep"] == "18013280"
    assert linha["geometry"] == "POINT(-47.425939 -23.480133)"
    assert pd.isna(linha["ds_observacao"])


def test_latitude_e_longitude_trocadas_sao_recusadas():
    with pytest.raises(ErroValidacao, match="fora do estado"):
        processar_locais(pd.DataFrame([_linha(latitude="-47.425939", longitude="-23.480133")]))


@pytest.mark.parametrize(
    "mudanca, mensagem",
    [
        ({"ds_precisao": "chute"}, "domínio"),
        ({"cd_mun": "3550308"}, "fora da RMS"),
        ({"latitude": ""}, "vazios"),
        ({"nu_cep": "1801"}, "CEP"),
    ],
)
def test_valores_invalidos_sao_recusados(mudanca, mensagem):
    with pytest.raises(ErroValidacao, match=mensagem):
        processar_locais(pd.DataFrame([_linha(**mudanca)]))


def test_local_duplicado_e_recusado():
    with pytest.raises(ErroValidacao, match="duplicadas"):
        processar_locais(pd.DataFrame([_linha(), _linha()]))
