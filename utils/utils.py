import os
from PyQt5.QtWidgets import QMessageBox

from autenticacao.helpers_autenticacao import get_db_connection


def montar_display_sala_variavel(nome, predio, anexo):
    # garante que tudo é str, não bytes
    if isinstance(nome, (bytes, bytearray)):
        nome = nome.decode("utf-8", errors="ignore")
    if isinstance(predio, (bytes, bytearray)):
        predio = predio.decode("utf-8", errors="ignore")
    if isinstance(anexo, (bytes, bytearray)):
        anexo = anexo.decode("utf-8", errors="ignore")

    display = nome or ""
    if predio:
        display += f" - {predio}"
    if anexo:
        display += f" / {anexo}"
    return display


def montar_display_sala_por_id(sala_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.nome, s.descricao, p.nome AS predio_nome, a.nome AS anexo_nome
        FROM salas s
        LEFT JOIN predios p ON s.predio_id = p.id
        LEFT JOIN anexos a ON s.anexo_id = a.id
        WHERE s.id = %s
    """, (sala_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return f"Sala {sala_id}"

    nome, descricao, predio, anexo = row
    partes = []

    if predio:
        partes.append(predio)
    if anexo:
        partes.append(anexo)
    if nome:
        partes.append(nome)
    display = " / ".join(partes)

    if descricao:
        display = f"{display} - {descricao}"

    return display


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
