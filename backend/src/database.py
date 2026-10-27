"""Conexão com o PostgreSQL/PostGIS (Supabase ou banco local).

A conexão é criada sob demanda, na primeira chamada de get_engine().
Assim é possível importar os módulos e rodar os testes das
transformações sem ter banco nem arquivo .env.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine


BASE_DIR = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Retorna o engine do SQLAlchemy, criado uma única vez."""

    load_dotenv(BASE_DIR / ".env")

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL não foi definida. Copie backend/.env.example para "
            "backend/.env e informe a conexão PostgreSQL/Supabase."
        )

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )
