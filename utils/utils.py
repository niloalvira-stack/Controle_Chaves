import os
from PyQt5.QtWidgets import QMessageBox

from autenticacao.helpers_autenticacao import get_db_connection


def montar_display_sala_variavel(nome, predio, anexo):
    display = nome
    if predio:
        display += f" - {predio}"
    if anexo:
        display += f" - {anexo}"
    return display


def montar_display_sala_por_id(sala_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.nome, p.nome, a.nome
        FROM salas s
        LEFT JOIN predios p ON s.predio_id = p.id
        LEFT JOIN anexos a ON s.anexo_id = a.id
        WHERE s.id = %s
    """, (sala_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return ""
    nome, predio, anexo = row
    return montar_display_sala_variavel(nome, predio, anexo)


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
