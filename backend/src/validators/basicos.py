"""Validações reutilizáveis. Todas lançam ValueError com mensagem clara.

Regra do projeto: se uma validação falha, a carga para e nada é gravado.
"""

from collections.abc import Iterable

import pandas as pd

from src.config.rms import CODIGOS_RMS


class ErroValidacao(ValueError):
    pass


def colunas_presentes(df: pd.DataFrame, colunas: Iterable[str], origem: str) -> None:
    faltantes = [c for c in colunas if c not in df.columns]

    if faltantes:
        raise ErroValidacao(
            f"{origem}: o arquivo mudou de estrutura. "
            f"Colunas esperadas não encontradas: {faltantes}"
        )


def apenas_rms(codigos: pd.Series, origem: str) -> None:
    fora = sorted(set(codigos.dropna()) - set(CODIGOS_RMS))

    if fora:
        raise ErroValidacao(f"{origem}: municípios fora da RMS: {fora[:10]}")


def todos_municipios_rms(codigos: Iterable[str], origem: str) -> None:
    encontrados = set(codigos)
    faltantes = sorted(set(CODIGOS_RMS) - encontrados)

    if faltantes:
        raise ErroValidacao(f"{origem}: municípios da RMS ausentes: {faltantes}")


def sem_duplicidade(df: pd.DataFrame, chave: list[str], origem: str) -> None:
    duplicados = df[df.duplicated(subset=chave, keep=False)]

    if not duplicados.empty:
        exemplo = duplicados[chave].head(5).to_dict(orient="records")
        raise ErroValidacao(
            f"{origem}: {len(duplicados)} linhas duplicadas na chave {chave}. "
            f"Exemplos: {exemplo}"
        )


def sem_nulos(df: pd.DataFrame, colunas: Iterable[str], origem: str) -> None:
    for coluna in colunas:
        quantidade = int(df[coluna].isna().sum())

        if quantidade:
            raise ErroValidacao(
                f"{origem}: coluna {coluna} tem {quantidade} valores vazios, "
                "mas é obrigatória no banco."
            )


def dominio(
    serie: pd.Series,
    permitidos: Iterable,
    origem: str,
    permitir_nulo: bool = False,
) -> None:
    valores = serie.dropna() if permitir_nulo else serie
    invalidos = sorted(set(valores) - set(permitidos), key=str)

    if invalidos:
        raise ErroValidacao(
            f"{origem}: valores fora do domínio em {serie.name}: {invalidos[:10]}"
        )


def nao_vazio(df: pd.DataFrame, origem: str) -> None:
    if df.empty:
        raise ErroValidacao(f"{origem}: nenhum registro encontrado no recorte da RMS.")
