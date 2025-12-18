import os
import sqlite3

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # se o arquivo fica na raiz do projeto
DB_NAME = os.path.join(BASE_DIR, "controle_chaves.db")


def get_connection():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
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
