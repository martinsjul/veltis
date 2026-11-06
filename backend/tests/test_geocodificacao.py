"""Testes da geocodificação das escolas (sem banco e sem baixar o CNEFE)."""

import pandas as pd
import pytest

from src.collectors.geocodificacao import selecionar_pontos, separar_endereco


@pytest.mark.parametrize(
    "endereco, cep, esperado",
    [
        # Catálogo do INEP: bairro depois do número, CEP e cidade no fim
        ("RUA NATAL, 340 JARDIM PAULISTANO. 18040-000 Sorocaba - SP", None,
         {"logradouro": "RUA NATAL", "numero": 340, "localidade": "JARDIM PAULISTANO", "cep": "18040000"}),
        # Número com ponto de milhar
        ("AVENIDA TIRADENTES, 1.817 PARQUE INDUSTRIAL. 13309-640 Itu - SP", None,
         {"logradouro": "AVENIDA TIRADENTES", "numero": 1817, "localidade": "PARQUE INDUSTRIAL", "cep": "13309640"}),
        # Sem número
        ("RUA JOAO VIEIRA CAMARGO, S/N VILA BARTH. 18205-600 Itapetininga - SP", None,
         {"logradouro": "RUA JOAO VIEIRA CAMARGO", "numero": None, "localidade": "VILA BARTH", "cep": "18205600"}),
        # SEDUC-SP: partes separadas por " - ", CEP em coluna própria
        ("AV PROFESSOR ARTHUR FONSECA, 633 - SALA 2 - JARDIM EMILIA", "18031005",
         {"logradouro": "AV PROFESSOR ARTHUR FONSECA", "numero": 633, "localidade": "JARDIM EMILIA", "cep": "18031005"}),
        # Só o logradouro
        ("ESTRADA DO BAIRRO DOS MORAES", None,
         {"logradouro": "ESTRADA DO BAIRRO DOS MORAES", "numero": None, "localidade": None, "cep": None}),
    ],
)
def test_separar_endereco(endereco, cep, esperado):
    assert separar_endereco(endereco, cep) == esperado


@pytest.mark.parametrize("vazio", [None, "", "   ", float("nan")])
def test_endereco_vazio(vazio):
    assert separar_endereco(vazio)["logradouro"] is None


def test_selecionar_pontos_aceita_so_numero_e_rua_com_desvio_pequeno():
    resultado = pd.DataFrame(
        {
            "co_entidade": [1, 2, 3, 4, 5, 6],
            "precisao": ["numero", "numero_aproximado", "logradouro", "logradouro", "cep", None],
            "desvio_metros": [6, 40, 350, 3000, 10, None],
            "lat": [-23.5, -23.5, -23.5, -23.5, -23.5, None],
            "lon": [-47.4, -47.4, -47.4, -47.4, -47.4, None],
        }
    )
    aceitos, motivos = selecionar_pontos(resultado)

    assert aceitos["co_entidade"].tolist() == [1, 2, 3]
    assert motivos["desvio grande demais"] == 1
    assert motivos["só achou o CEP, o bairro ou o município"] == 1
    assert motivos["endereço não encontrado"] == 1
