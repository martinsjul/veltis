"""Configurações da API, lidas do backend/.env (ou de variáveis de ambiente)."""

import os
from functools import lru_cache

from dotenv import load_dotenv

from src.database import BASE_DIR


ORIGENS_PADRAO = "http://localhost:5173,http://localhost:3000"


@lru_cache(maxsize=1)
def origens_cors() -> list[str]:
    """Endereços do frontend que podem chamar a API pelo navegador.

    No .env: VELTIS_CORS_ORIGENS=http://localhost:5173,https://veltis.exemplo.com
    """

    load_dotenv(BASE_DIR / ".env")
    bruto = os.getenv("VELTIS_CORS_ORIGENS", ORIGENS_PADRAO)
    return [origem.strip() for origem in bruto.split(",") if origem.strip()]
