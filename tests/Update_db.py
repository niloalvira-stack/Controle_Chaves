from database_module import execute_query

def update_schema():
    query = "ALTER TABLE usuarios ADD COLUMN primeiro_login INTEGER DEFAULT 1;"
    execute_query(query)
    print("Banco atualizado: coluna 'primeiro_login' adicionada.")

if __name__ == "__main__":
    update_schema()
