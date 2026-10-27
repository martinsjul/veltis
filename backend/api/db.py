"""Acesso ao banco pela API: somente leitura e com tempo limite.

Cada requisição recebe uma conexão própria, dentro de uma transação
READ ONLY. Mesmo que alguém tente, a API não consegue gravar nada.
"""

from collections.abc import Iterator
from typing import Any

from sqlalchemy import Connection, text

from src.database import get_engine


TEMPO_LIMITE_CONSULTA = "10s"


def conexao() -> Iterator[Connection]:
    """Dependência do FastAPI: entrega uma conexão só de leitura."""

    with get_engine().connect() as con:
        con.execute(text("SET TRANSACTION READ ONLY"))
        con.execute(text(f"SET LOCAL statement_timeout = '{TEMPO_LIMITE_CONSULTA}'"))
        try:
            yield con
        finally:
            con.rollback()


def linhas(con: Connection, sql: str, params: dict[str, Any] | None = None) -> list[dict]:
    return [dict(r) for r in con.execute(text(sql), params or {}).mappings()]


def linha(con: Connection, sql: str, params: dict[str, Any] | None = None) -> dict | None:
    resultado = con.execute(text(sql), params or {}).mappings().first()
    return dict(resultado) if resultado else None


def ano_mais_recente(con: Connection, tabela: str) -> int | None:
    """Último ano carregado (as tabelas podem guardar mais de uma edição)."""

    if tabela not in {"inep_escola", "mec_cursos"}:
        raise ValueError(f"Tabela não permitida: {tabela}")

    return con.execute(text(f"SELECT MAX(nu_ano_censo) FROM {tabela}")).scalar()
