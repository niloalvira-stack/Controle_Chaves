import sqlite3
import os
import sys  # Para .exe PyInstaller
from contextlib import closing

# Caminho robusto para DB (projeto ou dist/)
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Raiz do projeto
_DB_PATH = os.path.join(base_dir, "controle_chaves.db")

_current_user = None

def get_db_connection():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row  # row['Nome'], row['id'] etc.
    return conn

def set_current_user(user_dict):
    global _current_user
    _current_user = dict(user_dict)

def get_current_user():
    return _current_user

def is_admin():
    return bool(_current_user and _current_user.get("is_admin"))

def validar_login(login, senha=None):
    """
    Busca usuário por login na tabela 'usuarios' e popula _current_user
    com id, login, Nome e is_admin.
    """
    with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:
        print("DEBUG validar_login: login recebido =", repr(login))
        cur.execute(
            """
            SELECT id, login, Nome, is_admin
            FROM usuarios
            WHERE login = ?
            """,
            (login,),
        )
        row = cur.fetchone()
        print("DEBUG validar_login row retornado:", row)
        if row:
            user = dict(row)  # Automático: {'id':14, 'login':'rose', 'Nome':'Rose Silva', 'is_admin':False}
            print("DEBUG validar_login user:", user)
            set_current_user(user)
            return True
        return False
