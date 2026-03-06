import bcrypt
from PyQt5.QtWidgets import QMessageBox

from database_module import get_connection, execute_query  # usa o módulo padrão de BD


def create_user(login, nome, senha, is_admin=False):
    senha_hash = hash_password(senha)
    query = """
        INSERT INTO usuarios (login, nome, senha, primeiro_login, is_admin)
        VALUES (%s, %s, %s, %s, %s);
    """
    # primeiro_login TRUE no primeiro acesso, is_admin boolean
    execute_query(
        query,
        (login, nome, senha_hash, True, bool(is_admin)),
    )


def hash_password(password: str) -> str:
    """Gera o hash bcrypt da senha como string utf-8 para salvar no banco."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(stored_hash: str, password: str) -> bool:
    """
    Verifica se a senha fornecida bate com o hash armazenado.
    Somente aceita hash bcrypt (inicia com $2b$). Se não for hash, impede login.
    """
    if not stored_hash or not stored_hash.startswith("$2b$"):
        return False
    stored_hash_bytes = (
        stored_hash.encode("utf-8") if isinstance(stored_hash, str) else stored_hash
    )
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash_bytes)


def get_user_by_login(login: str):
    query = """
        SELECT id, login, nome, senha AS senha_hash, primeiro_login, is_admin
        FROM usuarios
        WHERE login = %s
    """
    # usa execute_query do database_module, que já abre RealDictCursor
    result = execute_query(query, (login,), fetchone=True)
    if result:
        return {
            "id": result["id"],
            "login": result["login"],
            "nome": result["nome"],
            "senha": result["senha_hash"],  # compatível com verify_password
            "primeiro_login": result["primeiro_login"],
            "is_admin": result["is_admin"],
        }
    return None


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

