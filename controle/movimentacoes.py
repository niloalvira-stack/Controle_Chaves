import sqlite3
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QFormLayout, QLineEdit, QMessageBox

DB_NAME = "controle_chaves.db"

# Cria a tabela se ela não existir
def criar_tabela_movimentacoes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chave TEXT NOT NULL,
        usuario TEXT NOT NULL,
        data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

# Lista todas as movimentações
def listar_movimentacoes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, chave, usuario, data_hora FROM movimentacoes ORDER BY data_hora DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Adiciona uma nova movimentação
def adicionar_movimentacao(chave, usuario):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO movimentacoes (chave, usuario) VALUES (?, ?)", (chave, usuario))
    conn.commit()
    conn.close()

# Opcional: classe PyQt5 para interface (se desejar usar na interface gráfica)
class MovimentacoesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        try:
            criar_tabela_movimentacoes()
        except Exception:
            pass
        self.carregar_movimentacoes()

    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        layout.addWidget(self.table)

        form_layout = QFormLayout()
        self.input_chave = QLineEdit()
        self.input_usuario = QLineEdit()
        form_layout.addRow("Chave:", self.input_chave)
        form_layout.addRow("Usuário:", self.input_usuario)
        layout.addLayout(form_layout)

        self.btn_add = QPushButton("Adicionar Movimentação")
        self.btn_add.clicked.connect(self.adicionar_movimentacao)
        layout.addWidget(self.btn_add)

        self.setLayout(layout)

    def carregar_movimentacoes(self):
        self.table.clear()
        movimentacoes = listar_movimentacoes()
        self.table.setRowCount(len(movimentacoes))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Chave", "Usuário", "Data/Hora"])
        for i, mov in enumerate(movimentacoes):
            for j, val in enumerate(mov):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        self.table.resizeColumnsToContents()

    def adicionar_movimentacao(self):
        chave = self.input_chave.text().strip()
        usuario = self.input_usuario.text().strip()
        if not chave or not usuario:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos!")
            return
        try:
            adicionar_movimentacao(chave, usuario)
            QMessageBox.information(self, "Sucesso", "Movimentação adicionada com sucesso!")
            self.input_chave.clear()
            self.input_usuario.clear()
            self.carregar_movimentacoes()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao adicionar movimentação: {e}")
