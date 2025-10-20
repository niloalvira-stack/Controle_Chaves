from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHBoxLayout, QMessageBox
)
from database_module import execute_query

class PrediosTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Gestão de Prédios")
        layout.addWidget(label)
        form_layout = QHBoxLayout()
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Nome do prédio")
        form_layout.addWidget(self.input_nome)
        self.input_endereco = QLineEdit()
        self.input_endereco.setPlaceholderText("Endereço")
        form_layout.addWidget(self.input_endereco)
        self.btn_add = QPushButton("Adicionar")
        self.btn_edit = QPushButton("Editar")
        self.btn_delete = QPushButton("Excluir")
        form_layout.addWidget(self.btn_add)
        form_layout.addWidget(self.btn_edit)
        form_layout.addWidget(self.btn_delete)
        layout.addLayout(form_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Endereço"])
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.SingleSelection)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.table.itemSelectionChanged.connect(self.preencher_campos_edicao)
        self.btn_add.clicked.connect(self.adicionar_predio)
        self.btn_edit.clicked.connect(self.editar_predio)
        self.btn_delete.clicked.connect(self.excluir_predio)
        self.criar_tabela_predios()
        self.load_predios()

    def criar_tabela_predios(self):
        execute_query(
            '''
            CREATE TABLE IF NOT EXISTS predios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                endereco TEXT
            )
            ''', ()
        )

    def load_predios(self):
        self.table.setRowCount(0)
        try:
            predios = execute_query("SELECT id, nome, endereco FROM predios ORDER BY nome", (), fetchall=True)
            self.table.setRowCount(len(predios))
            for i, predio in enumerate(predios):
                self.table.setItem(i, 0, QTableWidgetItem(str(predio["id"])))
                self.table.setItem(i, 1, QTableWidgetItem(predio["nome"]))
                self.table.setItem(i, 2, QTableWidgetItem(predio["endereco"] if predio["endereco"] else ""))
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao carregar prédios: {e}")

    def preencher_campos_edicao(self):
        selected = self.table.currentRow()
        if selected >= 0:
            self.input_nome.setText(self.table.item(selected, 1).text())
            self.input_endereco.setText(self.table.item(selected, 2).text())

    def adicionar_predio(self):
        nome = self.input_nome.text().strip()
        endereco = self.input_endereco.text().strip()
        if not nome:
            QMessageBox.warning(self, "Aviso", "O nome do prédio é obrigatório.")
            return
        try:
            execute_query("INSERT INTO predios (nome, endereco) VALUES (?, ?)", (nome, endereco))
            QMessageBox.information(self, "Sucesso", "Prédio adicionado com sucesso.")
            self.input_nome.clear()
            self.input_endereco.clear()
            self.load_predios()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao adicionar prédio: {e}")

    def editar_predio(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Erro", "Selecione um prédio para editar.")
            return
        predio_id = int(self.table.item(selected, 0).text())
        novo_nome = self.input_nome.text().strip()
        novo_endereco = self.input_endereco.text().strip()
        if not novo_nome:
            QMessageBox.warning(self, "Erro", "O nome do prédio não pode ser vazio.")
            return
        try:
            execute_query("UPDATE predios SET nome=?, endereco=? WHERE id=?", (novo_nome, novo_endereco, predio_id))
            QMessageBox.information(self, "Sucesso", "Prédio editado com sucesso.")
            self.input_nome.clear()
            self.input_endereco.clear()
            self.load_predios()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao editar prédio: {e}")

    def excluir_predio(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Erro", "Selecione um prédio para excluir.")
            return
        predio_id = int(self.table.item(selected, 0).text())
        try:
            execute_query("DELETE FROM predios WHERE id=?", (predio_id,))
            QMessageBox.information(self, "Sucesso", "Prédio excluído com sucesso.")
            self.input_nome.clear()
            self.input_endereco.clear()
            self.load_predios()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao excluir prédio: {e}")
