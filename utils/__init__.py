from PyQt6.QtWidgets import QMessageBox
from autenticacao.helpers_autenticacao import get_db_connection


# utils/__init__.py

def montar_display_sala_variavel(nome, predio=None, anexo=None):
    def _to_str(v):
        return v.decode("utf-8") if isinstance(v, (bytes, bytearray)) else v

    nome = _to_str(nome)
    predio = _to_str(predio)
    anexo = _to_str(anexo)

    display = nome or ""
    if predio:
        display += f" - {predio}"
    if anexo:
        display += f" ({anexo})"
    return display



def montar_display_sala_por_id(sala_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.nome, p.nome
        FROM salas s
        LEFT JOIN predios p ON s.predio_id = p.id
        WHERE s.id = %s
    """, (sala_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return ""
    nome, predio = row
    return montar_display_sala_variavel(nome, predio)


def show_info(title: str, message: str):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def show_warning(title: str, message: str):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()
