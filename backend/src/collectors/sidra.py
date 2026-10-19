"""Pipeline 2 - IBGE SIDRA (API de Dados Agregados v3) -> IBGE_DEMOGRAFICO.

Para cada indicador de src/config/indicadores_sidra.py:
consulta a API para os 27 municípios, transforma cada valor
(com suas classificações: sexo, idade...) em uma linha, valida e
grava com upsert pela chave única da tabela demográfica.

Executar sozinho:  python -m src.collectors.sidra [--forcar]
"""

import argparse
import json
from math import prod

import pandas as pd

from src.collectors.download import obter_json
from src.config.edicoes import URL_SIDRA
from src.config.indicadores_sidra import INDICADORES_SIDRA
from src.config.rms import CODIGOS_RMS
from src.loaders.carga import para_registros, upsert
from src.loaders.ingestao import Fonte, carga, hash_json
from src.transforms.sidra import chave_classificacao, classificacoes_json, converter_valor
from src.validators import basicos as validar


FONTE = Fonte(
    orgao="IBGE",
    nome="SIDRA",
    url_oficial=URL_SIDRA,
    periodicidade="Variável",
    observacao="API de Dados Agregados do IBGE.",
)

# A API recusa (HTTP 500) consultas acima de ~50 mil valores.
LIMITE_VALORES = 40_000


def montar_consulta(indicador: dict) -> tuple[str, dict]:
    url = (
        f"{URL_SIDRA}/{indicador['agregado']}"
        f"/periodos/{'|'.join(indicador['periodos'])}"
        f"/variaveis/{'|'.join(indicador['variaveis'])}"
    )

    parametros = {"localidades": f"N6[{','.join(CODIGOS_RMS)}]"}

    if indicador["classificacoes"]:
        parametros["classificacao"] = "|".join(
            f"{cid}[{','.join(categorias)}]"
            for cid, categorias in indicador["classificacoes"].items()
        )

    return url, parametros


def valores_esperados(indicador: dict) -> int:
    """municípios x períodos x variáveis x combinações de categorias."""

    combinacoes = prod(len(c) for c in indicador["classificacoes"].values()) or 1

    return (
        len(CODIGOS_RMS)
        * len(indicador["periodos"])
        * len(indicador["variaveis"])
        * combinacoes
    )


def transformar(dados: list, indicador: dict) -> pd.DataFrame:
    linhas = []

    for variavel in dados:
        for resultado in variavel["resultados"]:
            classificacoes = resultado["classificacoes"]
            chave = chave_classificacao(classificacoes)
            js = json.dumps(classificacoes_json(classificacoes), ensure_ascii=False)

            for serie in resultado["series"]:
                cd_mun = serie["localidade"]["id"]

                for periodo, bruto in serie["serie"].items():
                    valor, simbolo = converter_valor(bruto, variavel["unidade"])

                    linhas.append(
                        {
                            "cd_mun": cd_mun,
                            "co_periodo": str(periodo),
                            "cd_agregado": indicador["agregado"],
                            "cd_variavel": str(variavel["id"]),
                            "no_variavel": variavel["variavel"][:255],
                            "ds_unidade": (variavel["unidade"] or "")[:100] or None,
                            "ds_chave_classificacao": chave,
                            "js_classificacoes": js,
                            "vl_indicador": valor,
                            "ds_valor_original": simbolo,
                        }
                    )

    return pd.DataFrame(linhas)


def validar_indicador(df: pd.DataFrame, indicador: dict) -> None:
    origem = f"SIDRA {indicador['agregado']}"
    esperado = valores_esperados(indicador)

    if len(df) != esperado:
        raise validar.ErroValidacao(
            f"{origem}: esperados {esperado} valores, a API devolveu {len(df)}."
        )

    validar.apenas_rms(df["cd_mun"], origem)
    validar.todos_municipios_rms(df["cd_mun"], origem)
    validar.sem_duplicidade(
        df,
        ["cd_mun", "co_periodo", "cd_variavel", "ds_chave_classificacao"],
        origem,
    )

    periodos = set(df["co_periodo"])
    if periodos != set(indicador["periodos"]):
        raise validar.ErroValidacao(
            f"{origem}: períodos devolvidos {sorted(periodos)} "
            f"diferentes dos pedidos {indicador['periodos']}."
        )


def carregar_indicador(indicador: dict, forcar: bool = False) -> None:
    print(f"\nSIDRA {indicador['agregado']}: {indicador['descricao']}")

    esperado = valores_esperados(indicador)
    if esperado > LIMITE_VALORES:
        raise ValueError(
            f"Consulta da tabela {indicador['agregado']} teria {esperado} valores; "
            f"o limite seguro é {LIMITE_VALORES}. Divida o indicador."
        )

    url, parametros = montar_consulta(indicador)
    dados = obter_json(url, parametros)

    if not dados:
        raise ValueError(f"A API do SIDRA não retornou dados para {indicador['agregado']}.")

    arquivo = (
        f"API_SIDRA_{indicador['agregado']}"
        f"_{'-'.join(indicador['variaveis'])}"
        f"_{'-'.join(indicador['periodos'])}.json"
    )

    with carga(
        FONTE,
        periodo="|".join(indicador["periodos"]),
        versao=f"SIDRA agregado {indicador['agregado']}",
        arquivo=arquivo,
        hash_arquivo=hash_json(dados),
        forcar=forcar,
    ) as ing:
        if ing is None:
            return

        df = transformar(dados, indicador)
        validar_indicador(df, indicador)
        df["id_ingestao"] = ing.id_ingestao

        carregados = upsert(
            ing.conexao,
            "ibge_demografico",
            para_registros(df),
            chave=[
                "cd_mun", "co_periodo", "cd_agregado",
                "cd_variavel", "ds_chave_classificacao",
            ],
            expressoes={"js_classificacoes": "CAST(:js_classificacoes AS JSONB)"},
        )

        simbolos = int(df["ds_valor_original"].notna().sum())
        ing.registrar_contagens(
            lidos=len(df),
            carregados=carregados,
            observacao=(
                f"{indicador['descricao']}. "
                f"{simbolos} valores com símbolo especial do IBGE."
            ),
        )


def executar_pipeline(forcar: bool = False) -> None:
    print("\n=== IBGE - SIDRA ===")

    for indicador in INDICADORES_SIDRA:
        carregar_indicador(indicador, forcar=forcar)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--forcar", action="store_true")
    executar_pipeline(forcar=parser.parse_args().forcar)
