"""Transformações específicas da API de Dados Agregados (SIDRA) do IBGE."""

from decimal import Decimal, InvalidOperation


# Símbolos especiais do IBGE
#   -    zero absoluto (não resultante de arredondamento)
#   X    valor inibido para não identificar o informante
#   ..   não se aplica
#   ...  dado não disponível
SIMBOLOS_ESPECIAIS = {"-", "X", "..", "..."}

# Unidades de taxa/razão/média: nelas "-" significa "não calculável",
# não zero (ex.: taxa de frequência de um grupo sem população).
UNIDADES_NAO_SOMAVEIS = {"%", "anos", "razão", "razao", "hab/km²", "hab/km2"}


def chave_classificacao(classificacoes: list[dict]) -> str:
    """Chave canônica: pares id:categoria ordenados pelo id numérico.

    [] -> ''   |   Sexo=Homens, Idade=0-4 -> '2:4|287:93070'
    Independe da ordem em que a API devolve as classificações.
    """

    pares = []

    for classificacao in sorted(classificacoes, key=lambda c: int(c["id"])):
        categorias = list(classificacao["categoria"].keys())

        if len(categorias) != 1:
            raise ValueError(
                f"Classificação {classificacao['id']} veio com "
                f"{len(categorias)} categorias; esperado 1."
            )

        pares.append(f"{classificacao['id']}:{categorias[0]}")

    return "|".join(pares)


def classificacoes_json(classificacoes: list[dict]) -> list[dict]:
    """Formato gravado em JS_CLASSIFICACOES."""

    saida = []

    for classificacao in sorted(classificacoes, key=lambda c: int(c["id"])):
        codigo, nome = next(iter(classificacao["categoria"].items()))
        saida.append(
            {
                "cd_classificacao": str(classificacao["id"]),
                "no_classificacao": classificacao["nome"],
                "cd_categoria": str(codigo),
                "no_categoria": nome,
            }
        )

    return saida


def converter_valor(bruto, unidade: str | None) -> tuple[Decimal | None, str | None]:
    """Valor da API (sempre texto) -> (número, símbolo original).

    '723682' -> (723682, None)
    '-' em contagem -> (0, '-')      '-' em taxa -> (None, '-')
    'X', '..', '...' -> (None, símbolo)
    """

    if bruto is None:
        return None, None

    texto = str(bruto).strip()

    if texto in SIMBOLOS_ESPECIAIS:
        if texto == "-" and (unidade or "").strip().lower() not in UNIDADES_NAO_SOMAVEIS:
            return Decimal(0), texto
        return None, texto

    try:
        return Decimal(texto), None
    except InvalidOperation as erro:
        raise ValueError(f"Valor inesperado do SIDRA: {bruto!r}") from erro
