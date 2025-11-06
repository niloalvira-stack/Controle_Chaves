import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QFormLayout, QLineEdit, QMessageBox
)
from PyQt5.QtCore import QTimer, Qt
from datetime import datetime
import pytz

DB_NAME = "controle_chaves.db"

def data_hora_brasil():
    return datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")

def criar_tabela_movimentacoes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT NOT NULL,
            usuario TEXT NOT NULL,
            data_retirada TIMESTAMP,
            data_retorno TIMESTAMP,
            status TEXT DEFAULT 'disponível'
        )
    """)
    conn.commit()
    conn.close()

def listar_movimentacoes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, chave, usuario, data_retirada, data_retorno, status
        FROM movimentacoes
        ORDER BY data_retirada DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def registrar_retirada(chave, usuario):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO movimentacoes (chave, usuario, data_retirada, status)
        VALUES (?, ?, ?, 'indisponível')
    """, (chave, usuario, data_hora_brasil()))
    conn.commit()
    conn.close()

def registrar_devolucao(mov_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE movimentacoes
        SET data_retorno = ?, status = 'disponível'
        WHERE id = ? AND status = 'indisponível'
    """, (data_hora_brasil(), mov_id))
    conn.commit()
    conn.close()


class MovimentacoesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        criar_tabela_movimentacoes()
        self.carregar_movimentacoes()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.carregar_movimentacoes)
        self.timer.start(5000)

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Chave", "Usuário", "Retirada", "Devolução", "Status"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        form_layout = QFormLayout()
        self.input_chave = QLineEdit()
        self.input_usuario = QLineEdit()
        form_layout.addRow("Chave:", self.input_chave)
        form_layout.addRow("Usuário:", self.input_usuario)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.btn_retirar = QPushButton("Registrar Retirada")
        self.btn_retirar.clicked.connect(self.adicionar_movimentacao)
        btn_layout.addWidget(self.btn_retirar)
        self.btn_devolver = QPushButton("Registrar Devolução")
        self.btn_devolver.clicked.connect(self.devolver_selecionada)
        btn_layout.addWidget(self.btn_devolver)
        layout.addLayout(btn_layout)

    def carregar_movimentacoes(self):
        self.table.setRowCount(0)
        try:
            movimentacoes = listar_movimentacoes()
            for row_data in movimentacoes:
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                for col_idx, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value if value else ""))
                    if col_idx == 5:  # status
                        if value == "disponível":
                            item.setBackground(Qt.green)
                        else:
                            item.setBackground(Qt.red)
                    self.table.setItem(row_idx, col_idx, item)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar movimentações:\n{e}")

    def adicionar_movimentacao(self):
        chave = self.input_chave.text().strip()
        usuario = self.input_usuario.text().strip()
        if not chave or not usuario:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos!")
            return
        try:
            registrar_retirada(chave, usuario)
            QMessageBox.information(self, "Sucesso", f"Retirada registrada para a chave '{chave}'!")
            self.input_chave.clear()
            self.input_usuario.clear()
            self.carregar_movimentacoes()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao registrar retirada:\n{e}")

    def devolver_selecionada(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Atenção", "Selecione uma movimentação para registrar devolução!")
            return
        mov_id = int(self.table.item(selected[0].row(), 0).text())
        status = self.table.item(selected[0].row(), 5).text()
        if status == "disponível":
            QMessageBox.information(self, "Info", "Esta movimentação já está devolvida!")
            return
        try:
            registrar_devolucao(mov_id)
            QMessageBox.information(self, "Sucesso", "Devolução registrada!")
            self.carregar_movimentacoes()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao registrar devolução:\n{e}")


def py():
    return None
