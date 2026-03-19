# database_module.py

import psycopg  # psycopg3
from utils.config_app import get_db_config


def get_connection():
    """
    Abre conexão com PostgreSQL usando os dados do config.ini
    (host, port, dbname, user, password).
    """
    cfg = get_db_config()

    try:
        conn = psycopg.connect(**cfg)
        return conn
    except psycopg.Error as e:
        print(f"Erro ao conectar no banco de dados: {e}")
        return None
