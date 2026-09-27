import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não foi definida. Copie backend/.env.example para backend/.env "
        "e informe a conexão PostgreSQL/Supabase."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)