# autenticacao/helpers_autenticacao.py

import psycopg  # psycopg3


def get_db_connection():
    """
    Retorna uma conexão com o banco PostgreSQL 'controle_chaves'.
    Ajuste host/user/password se necessário.
    """
    return psycopg.connect(
        host="localhost",
        port=5432,
        dbname="controle_chaves",
        user="postgres",
        password="123456",
    )
