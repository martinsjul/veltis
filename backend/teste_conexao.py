from src.database import engine

with engine.connect() as conexao:
    print("Conexão com o Supabase realizada com sucesso.")