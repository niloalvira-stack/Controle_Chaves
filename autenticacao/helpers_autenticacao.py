# autenticacao/helpers_autenticacao.py

import psycopg
from utils.config_app import get_db_config

_DB_CONFIG = get_db_config()


def get_db_connection():
    """
    Retorna conexão com o PostgreSQL usando os dados do config.ini.
    """
    return psycopg.connect(**_DB_CONFIG)
