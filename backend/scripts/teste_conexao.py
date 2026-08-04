import psycopg2

# Endereço do banco no Supabase
conexao_string = ""
try:
    # Tenta conectar no banco
    conn = psycopg2.connect(conexao_string)
    cursor = conn.cursor()
    
    # Testa listando as tabelas que criamos
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    
    tabelas = cursor.fetchall()
    
    print("Conexão funcionando!")
    print("Tabelas encontradas no banco:")
    for tabela in tabelas:
        print(f"   - {tabela[0]}")
    
    cursor.close()
    conn.close()

except Exception as e:
    print(f"Erro: {e}")