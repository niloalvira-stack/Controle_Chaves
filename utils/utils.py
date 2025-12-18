import os
import sqlite3
from PyQt5.QtWidgets import QMessageBox

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DB_NAME = os.path.join(BASE_DIR, "controle_chaves.db")


def montar_display_sala_variavel(nome, predio, anexo):
    display = nome
    if predio:
        display += f" - {predio}"
    if anexo:
        display += f" - {anexo}"
    return display


def montar_display_sala_por_id(sala_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.nome, p.nome, a.nome
        FROM salas s
        LEFT JOIN predios p ON s.predio_id = p.id
        LEFT JOIN anexos a ON s.anexo_id = a.id
        WHERE s.id = ?
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


