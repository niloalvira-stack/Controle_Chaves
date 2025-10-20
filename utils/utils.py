from database_module import execute_query
from PyQt5.QtWidgets import QMessageBox

def safe_count(query, params=()):
    """Executa query COUNT(*) com segurança, retornando 0 em caso de erro."""
    try:
        result = execute_query(query, params, fetchone=True)
        if result:
            return result[0]
        return 0
    except Exception:
        return 0

def show_info(title: str, message: str):
    """Exibe caixa de mensagem informativa na GUI."""
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
