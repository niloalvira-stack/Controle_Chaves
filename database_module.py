# database_module.py

import traceback
import psycopg
from psycopg.rows import dict_row

from utils.config_app import get_db_config


def get_connection():
    cfg = get_db_config()

    try:
        conn = psycopg.connect(
            host=cfg["host"],
            port=cfg["port"],
            dbname=cfg["dbname"],
            user=cfg["user"],
            password=cfg["password"],
            row_factory=dict_row
        )
        return conn
    except psycopg.Error as e:
        print(f"Erro ao conectar no banco de dados: {e}")
        traceback.print_exc()
        return None


def execute_query(query, params=(), fetchone=False):
    conn = get_connection()
    if conn is None:
        raise Exception("Não foi possível conectar ao banco de dados.")

    try:
        with conn.cursor() as cur:
            cur.execute(query, params)

            if cur.description is not None:
                if fetchone:
                    return cur.fetchone()
                return cur.fetchall()

            conn.commit()
            return None

    except Exception as e:
        conn.rollback()
        print(f"Erro ao executar query: {e}")
        traceback.print_exc()
        raise
    finally:
        conn.close()


get_db_connection = get_connection