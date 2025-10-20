from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QFormLayout, QHBoxLayout, QMessageBox
)
from database_module import execute_query

class SalasTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.label = QLabel("Gerenciamento de Salas")
        self.layout.addWidget(self.label)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.SingleSelection)
        self.layout.addWidget(self.table)
        self.table.itemSelectionChanged.connect(self.preencher_campos_edicao)
        form_layout = QFormLayout()
        self.input_nome = QLineEdit()
        self.input_descricao = QLineEdit()
        form_layout.addRow("Nome:", self.input_nome)
        form_layout.addRow("Descrição:", self.input_descricao)
        self.layout.addLayout(form_layout)
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Adicionar Sala")
        self.btn_edit = QPushButton("Editar Sala")
        self.btn_delete = QPushButton("Excluir Sala")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        self.layout.addLayout(btn_layout)
        self.btn_add.clicked.connect(self.adicionar_sala)
        self.btn_edit.clicked.connect(self.editar_sala)
        self.btn_delete.clicked.connect(self.excluir_sala)
        self.criar_tabela_salas()
        self.carregar_salas()

    def criar_tabela_salas(self):
        execute_query(
            '''
            CREATE TABLE IF NOT EXISTS salas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                descricao TEXT
            )
            ''', ()
        )

    def carregar_salas(self):
        self.table.clear()
        rows = execute_query("SELECT id, nome, descricao FROM salas ORDER BY nome", (), fetchall=True)
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Descrição"])
        for i, sala in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(sala["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(sala["nome"]))
            self.table.setItem(i, 2, QTableWidgetItem(sala["descricao"]))
        self.table.resizeColumnsToContents()

    def adicionar_sala(self):
        nome = self.input_nome.text().strip()
        descricao = self.input_descricao.text().strip()
        if not nome:
            QMessageBox.warning(self, "Erro", "O nome da sala é obrigatório.")
            return
        try:
            execute_query("INSERT INTO salas (nome, descricao) VALUES (?, ?)", (nome, descricao))
            QMessageBox.information(self, "Sucesso", "Sala adicionada com sucesso.")
            self.input_nome.clear()
            self.input_descricao.clear()
            self.carregar_salas()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao adicionar sala: {e}")

    def preencher_campos_edicao(self):
        selected = self.table.currentRow()
        if selected >= 0:
            self.input_nome.setText(self.table.item(selected, 1).text())
            self.input_descricao.setText(self.table.item(selected, 2).text())

    def editar_sala(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Erro", "Selecione uma sala para editar.")
            return
        sala_id = int(self.table.item(selected, 0).text())
        novo_nome = self.input_nome.text().strip()
        nova_descricao = self.input_descricao.text().strip()
        if not novo_nome:
            QMessageBox.warning(self, "Erro", "O nome da sala não pode ser vazio.")
            return
        try:
            execute_query(
                "UPDATE salas SET nome=?, descricao=? WHERE id=?",
                (novo_nome, nova_descricao, sala_id)
            )
            QMessageBox.information(self, "Sucesso", "Sala editada com sucesso.")
            self.input_nome.clear()
            self.input_descricao.clear()
            self.carregar_salas()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao editar sala: {e}")

    def excluir_sala(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Erro", "Selecione uma sala para excluir.")
            return
        sala_id = int(self.table.item(selected, 0).text())
        try:
            execute_query("DELETE FROM salas WHERE id=?", (sala_id,))
            QMessageBox.information(self, "Sucesso", "Sala excluída com sucesso.")
            self.input_nome.clear()
            self.input_descricao.clear()
            self.carregar_salas()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao excluir sala: {e}")
