import os
from PyQt6.QtWidgets import QMessageBox

from autenticacao.helpers_autenticacao import get_db_connection
from datetime import datetime, timedelta, timezone


def _parse_datetime(value):
    if not value:
        return None

    # ✅ Se já é datetime COM fuso → REMOVE o fuso!
    if isinstance(value, datetime):
        if hasattr(value, 'tzinfo') and value.tzinfo:
            return value.replace(tzinfo=None)  # ← CHAVE DO PROBLEMA!
        return value

    texto = str(value).strip()

    # ✅ CORTA o fuso do final antes de converter!
    if len(texto) > 19 and (texto[19] in '+-' or texto.endswith('Z')):
        texto = texto[:19]  # Fica só: "2026-09-09 08:00:00"

    formatos = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    )

    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt)
        except Exception:
            continue

    try:
        # Também remove fuso no fromisoformat
        dt = datetime.fromisoformat(texto.replace("Z", "+00:00"))
        if hasattr(dt, 'tzinfo') and dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        return None

def formatar_data_br(data):
    """Formata data para DD/MM/AAAA HH:MM — BANCO JÁ ESTÁ CERTO!"""
    if not data:
        return ""

    # ✅ Se for objeto datetime — MOSTRA DIRETO!
    if hasattr(data, "strftime"):
        return data.strftime("%d/%m/%Y %H:%M")

    # ✅ Se for texto — remove o "-03" do final e formata
    if isinstance(data, str):
        try:
            data_limpa = data[:19]  # Pega "AAAA-MM-DD HH:MM:SS"
            dt = datetime.strptime(data_limpa, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return data[:16] if len(data) >= 16 else data

    return str(data)[:16]

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
    msg.exec()


def show_warning(title: str, message: str):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()
