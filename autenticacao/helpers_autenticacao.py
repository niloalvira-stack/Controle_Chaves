# autenticacao/helpers_autenticacao.py
import sqlite3
from contextlib import closing

# ATENÇÃO: confirme se este é o caminho exato do SEU banco
# Se o arquivo estiver em outra pasta, ajuste o caminho.
_DB_PATH = "controle_chaves.db"

_current_user = None  # {"id": int, "login": str, "is_admin": bool}


def get_db_connection():
    return sqlite3.connect(_DB_PATH)


def set_current_user(user_dict):
    global _current_user
    _current_user = user_dict


def get_current_user():
    return _current_user


def is_admin():
    return bool(_current_user and _current_user.get("is_admin"))


def validar_login(login, senha=None):
    """
    Busca usuário por login na tabela 'usuarios' e popula _current_user
    com id, login e is_admin. A senha já foi validada fora.
    """
    with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:
        print("DEBUG validar_login: login recebido =", repr(login))
        cur.execute(
            """
            SELECT id, login, is_admin
            FROM usuarios
            WHERE login = ?
            """,
            (login,),
        )
        row = cur.fetchone()
        print("DEBUG validar_login row retornado:", row)
        if row:
            user = {
                "id": row[0],
                "login": row[1],
                "is_admin": bool(row[2]),
            }
            print("DEBUG validar_login user:", user)
            set_current_user(user)
            return True
        return False
