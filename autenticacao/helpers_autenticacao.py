# autenticacao/helpers_autenticacao.py

from database_module import get_connection


def get_db_connection():
    """
    Retorna uma conexão usando o mesmo config.ini / database_module.
    """
    return get_connection()
