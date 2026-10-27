"""Gravação em lote no banco (upsert) a partir de DataFrames."""

import re

import pandas as pd
from sqlalchemy import text


_IDENTIFICADOR = re.compile(r"^[a-z_][a-z0-9_]*$")


def _validar_identificador(nome: str) -> str:
    if not _IDENTIFICADOR.match(nome):
        raise ValueError(f"Identificador SQL inválido: {nome!r}")
    return nome


def para_registros(df: pd.DataFrame) -> list[dict]:
    """Converte o DataFrame em lista de dicts com None no lugar de NaN/NA.

    O astype(object) é necessário: no pandas 3, df.where(..., None)
    em colunas numéricas mantém NaN, e NaN não entra em colunas
    BOOLEAN/SMALLINT do PostgreSQL.
    """

    return (
        df.astype(object)
        .where(df.notna(), None)
        .to_dict(orient="records")
    )


def upsert(
    conexao,
    tabela: str,
    registros: list[dict],
    chave: list[str],
    expressoes: dict[str, str] | None = None,
    lote: int = 1000,
) -> int:
    """INSERT ... ON CONFLICT (chave) DO UPDATE em lotes.

    expressoes permite trocar o placeholder de uma coluna por uma
    expressão SQL, ex.: {"geometry": "ST_GeomFromText(:geometry, 4674)"}.
    Retorna a quantidade de registros enviados.
    """

    if not registros:
        return 0

    expressoes = expressoes or {}
    tabela = _validar_identificador(tabela)
    colunas = [_validar_identificador(c) for c in registros[0].keys()]
    chave = [_validar_identificador(c) for c in chave]

    valores = [expressoes.get(c, f":{c}") for c in colunas]
    atualizar = [c for c in colunas if c not in chave]

    acao = (
        "DO UPDATE SET " + ", ".join(f"{c} = EXCLUDED.{c}" for c in atualizar)
        if atualizar
        else "DO NOTHING"
    )

    sql = text(
        f"INSERT INTO {tabela} ({', '.join(colunas)}) "
        f"VALUES ({', '.join(valores)}) "
        f"ON CONFLICT ({', '.join(chave)}) {acao}"
    )

    for inicio in range(0, len(registros), lote):
        conexao.execute(sql, registros[inicio:inicio + lote])

    return len(registros)
