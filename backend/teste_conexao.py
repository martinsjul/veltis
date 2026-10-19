"""Confere se a conexão com o banco (Supabase ou local) funciona.

    python teste_conexao.py
"""

from sqlalchemy import text

from src.database import get_engine


with get_engine().connect() as conexao:
    versao = conexao.execute(text("SELECT version()")).scalar_one()
    postgis = conexao.execute(text("SELECT postgis_version()")).scalar_one()

print("Conexão realizada com sucesso.")
print(f"PostgreSQL: {versao.split(',')[0]}")
print(f"PostGIS: {postgis}")
