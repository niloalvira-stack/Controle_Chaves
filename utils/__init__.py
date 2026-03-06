from PyQt5.QtWidgets import QMessageBox


def montar_display_sala_variavel(nome, predio, anexo=None):
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
    msg.exec_()


def show_warning(title: str, message: str):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec_()
