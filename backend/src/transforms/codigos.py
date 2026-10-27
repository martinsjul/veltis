"""Conversões reutilizáveis entre o formato das fontes e o do banco."""

import re
import unicodedata

import pandas as pd


VAZIOS = {"", "nan", "none", "null", "na", "<na>"}


def como_objeto(valores, index=None) -> pd.Series:
    """Series de dtype object: preserva None (o pandas 3 trocaria por NaN)."""

    return pd.Series(list(valores), index=index, dtype=object)


def _e_vazio(valor) -> bool:
    if valor is None:
        return True
    if isinstance(valor, float) and pd.isna(valor):
        return True
    if valor is pd.NA:
        return True
    return isinstance(valor, str) and valor.strip().lower() in VAZIOS


def codigo_municipio(serie: pd.Series) -> pd.Series:
    """Código IBGE com 7 dígitos, como texto ('3552205')."""

    return (
        serie.astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(7)
    )


def para_booleano(serie: pd.Series) -> pd.Series:
    """0/1 (texto ou número) -> False/True. Vazio -> None.

    Qualquer outro valor é erro: melhor parar a carga do que gravar
    um indicador errado.
    """

    def converter(valor):
        if _e_vazio(valor):
            return None

        texto = str(valor).strip()
        texto = texto[:-2] if texto.endswith(".0") else texto

        if texto == "0":
            return False
        if texto == "1":
            return True

        raise ValueError(f"Valor inesperado para indicador 0/1: {valor!r}")

    return como_objeto((converter(v) for v in serie), serie.index)


def para_inteiro(serie: pd.Series) -> pd.Series:
    """Texto ou número -> inteiro (Int64, aceita nulo)."""

    limpa = serie.map(lambda v: None if _e_vazio(v) else str(v).strip())
    return pd.to_numeric(limpa, errors="raise").astype("Int64")


def para_texto(serie: pd.Series, tamanho_maximo: int | None = None) -> pd.Series:
    """Remove espaços nas pontas; vazio -> None; corta no tamanho da coluna."""

    def converter(valor):
        if _e_vazio(valor):
            return None

        texto = str(valor).strip().strip('"').strip()

        if not texto:
            return None
        if tamanho_maximo:
            texto = texto[:tamanho_maximo]

        return texto

    return como_objeto((converter(v) for v in serie), serie.index)


def somente_digitos(valor, tamanho: int | None = None) -> str | None:
    """'18.035-000' -> '18035000'. Completa com zeros à esquerda."""

    if _e_vazio(valor):
        return None

    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)

    digitos = re.sub(r"\D", "", str(valor))

    if not digitos:
        return None
    if tamanho:
        digitos = digitos.zfill(tamanho)[:tamanho]

    return digitos


def para_coordenada(valor) -> float | None:
    """Aceita '-23,5017' e '-23.5017'. Vazio ou inválido -> None."""

    if _e_vazio(valor):
        return None

    texto = str(valor).strip().replace(" ", "")

    # "1.234,56" não é coordenada; aqui só tratamos vírgula decimal simples.
    if texto.count(",") == 1 and "." not in texto:
        texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return None


def normalizar_nome(texto) -> str:
    """'Código INEP ' -> 'codigo_inep'. Usado para achar colunas."""

    if texto is None:
        return ""

    sem_acento = (
        unicodedata.normalize("NFKD", str(texto))
        .encode("ascii", "ignore")
        .decode("ascii")
    )

    return re.sub(r"[^a-z0-9]+", "_", sem_acento.lower()).strip("_")
