# autenticacao/autenticacao.py

import bcrypt
from PyQt5.QtWidgets import QMessageBox
import psycopg  # psycopg3
import psycopg.rows

from utils.config_app import get_db_config

DB_CONFIG = get_db_config()


def execute_query(query, params=(), fetchone=False):
    """
    Executa query no PostgreSQL.
    - Para SELECT, retorna dict (fetchone=True) ou lista de dicts.
    - Para INSERT/UPDATE/DELETE, retorna None (e apenas faz commit).
    """
    conn = None
    try:
        conn = psycopg.connect(**DB_CONFIG)
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        cur.execute(query, params)

        # Descobre se o comando é SELECT
        is_select = query.lstrip().upper().startswith("SELECT")

        if is_select:
            if fetchone:
                result = cur.fetchone()
            else:
                result = cur.fetchall()
        else:
            result = None  # UPDATE/INSERT/DELETE não retornam linhas

        conn.commit()
        print("DEBUG execute_query OK, rowcount:", cur.rowcount)
        return result
    except Exception as e:
        print(f"Erro ao executar query: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()


def create_user(login, nome, senha, is_admin=False):
    senha_hash = hash_password(senha)
    query = """
        INSERT INTO usuarios (login, nome, senha, primeiro_login, is_admin)
        VALUES (%s, %s, %s, %s, %s);
    """
    execute_query(query, (login, nome, senha_hash, True, bool(is_admin)))


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(stored_hash: str, password: str) -> bool:
    if not stored_hash or not stored_hash.startswith("$2b$"):
        return False
    stored_hash_bytes = stored_hash.encode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash_bytes)


def get_user_by_login(login: str):
    query = """
        SELECT id, login, nome, senha AS senha_hash, primeiro_login, is_admin
        FROM usuarios
        WHERE login = %s
    """
    result = execute_query(query, (login,), fetchone=True)
    print("DEBUG get_user_by_login: login =", login, "result =", result)

    # Se não encontrou usuário, evita acessar campos de None
    if result is None:
        print("DEBUG get_user_by_login: usuário não encontrado para login:", login)
        return None

    # Aqui já sabemos que result é um dict
    print(
        "DEBUG get_user_by_login raw primeiro_login:",
        result["primeiro_login"],
        type(result["primeiro_login"]),
    )

    # Normaliza possíveis bytes -> str
    def _to_str(v):
        return v.decode("utf-8") if isinstance(v, (bytes, bytearray)) else v

    return {
        "id": result["id"],
        "login": _to_str(result["login"]),
        "nome": _to_str(result["nome"]),
        "senha": _to_str(result["senha_hash"]),
        "primeiro_login": result["primeiro_login"],
        "is_admin": result["is_admin"],
    }


def show_info(title: str, message: str):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec_()


def show_warning(title: str, message: str):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec_()
