import sqlite3

DB_NAME = "controle_chaves.db"

def get_connection():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
        return conn
    except sqlite3.Error as e:
        print(f"Erro ao conectar no banco de dados: {e}")
        return None

def execute_query(query, params=(), fetchone=False, fetchall=False):
    conn = get_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()

        return None
    except sqlite3.Error as e:
        print(f"Erro ao executar query: {e}")
        return None
    finally:
        conn.close()
