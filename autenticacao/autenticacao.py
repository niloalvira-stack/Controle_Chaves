import bcrypt
from PyQt5.QtWidgets import QMessageBox
from database_module import execute_query

def create_user(login, nome, senha, is_admin=0):
    senha_hash = hash_password(senha)
    query = '''
    INSERT INTO usuarios (login, nome, senha, is_admin, primeiro_login)
    VALUES (?, ?, ?, ?, 1);
    '''
    execute_query(query, (login, nome, senha_hash, is_admin))

def hash_password(password: str) -> str:
    """Gera o hash bcrypt da senha como string utf-8 para salvar no banco."""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def verify_password(stored_hash: str, password: str) -> bool:
    """
    Verifica se a senha fornecida bate com o hash armazenado.
    Somente aceita hash bcrypt (inicia com $2b$). Se não for hash, impede login.
    """
    if not stored_hash or not stored_hash.startswith("$2b$"):
        # Não está hasheada corretamente
        return False
    if isinstance(stored_hash, str):
        stored_hash_bytes = stored_hash.encode('utf-8')
    else:
        stored_hash_bytes = stored_hash
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash_bytes)

def get_user_by_login(login: str):
    query = "SELECT id, login, nome, senha, primeiro_login, is_admin FROM usuarios WHERE login = ?"
    result = execute_query(query, (login,), fetchone=True)
    return dict(result) if result else None

def show_info(title: str, message: str):
    """Exibe caixa de mensagem Informativa na GUI."""
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec_()

def show_warning(title: str, message: str):
    """Exibe caixa de mensagem de aviso na GUI."""
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec_()
