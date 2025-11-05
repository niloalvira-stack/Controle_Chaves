from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QFormLayout, QHBoxLayout, QMessageBox, QComboBox
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
        self.combo_predios = QComboBox()
        self.combo_anexos = QComboBox()

        form_layout.addRow("Nome:", self.input_nome)
        form_layout.addRow("Descrição:", self.input_descricao)
        form_layout.addRow("Prédio:", self.combo_predios)
        form_layout.addRow("Anexo:", self.combo_anexos)
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
        self.load_predios_combobox()
        self.load_anexos_combobox()
        self.carregar_salas()

    def criar_tabela_salas(self):
        execute_query(
            '''
            CREATE TABLE IF NOT EXISTS salas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                descricao TEXT,
                predio_id INTEGER,
                anexo_id INTEGER,
                FOREIGN KEY(predio_id) REFERENCES predios(id),
                FOREIGN KEY(anexo_id) REFERENCES anexos(id)
            )
            ''', ()
        )

    def load_predios_combobox(self):
        self.combo_predios.clear()
        self.combo_predios.addItem("Nenhum", None)
        predios = execute_query("SELECT id, nome FROM predios ORDER BY nome ASC", (), fetchall=True)
        for predio in predios:
            self.combo_predios.addItem(predio["nome"], predio["id"])

    def load_anexos_combobox(self):
        self.combo_anexos.clear()
        self.combo_anexos.addItem("Nenhum", None)
        anexos = execute_query("SELECT id, nome FROM anexos ORDER BY nome ASC", (), fetchall=True)
        for anexo in anexos:
            self.combo_anexos.addItem(anexo["nome"], anexo["id"])

    def carregar_salas(self):
        self.table.clear()
        rows = execute_query(
            "SELECT s.id, s.nome, s.descricao, p.nome as predio_nome, a.nome as anexo_nome FROM salas s "
            "LEFT JOIN predios p ON s.predio_id = p.id LEFT JOIN anexos a ON s.anexo_id = a.id ORDER BY s.nome",
            (), fetchall=True
        )
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Descrição", "Prédio", "Anexo"])
        for i, sala in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(sala["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(sala["nome"]))
            self.table.setItem(i, 2, QTableWidgetItem(sala["descricao"]))
            self.table.setItem(i, 3, QTableWidgetItem(sala["predio_nome"] or "Nenhum"))
            self.table.setItem(i, 4, QTableWidgetItem(sala["anexo_nome"] or "Nenhum"))
        self.table.resizeColumnsToContents()

    def adicionar_sala(self):
        nome = self.input_nome.text().strip()
        descricao = self.input_descricao.text().strip()
        predio_id = self.combo_predios.currentData()
        anexo_id = self.combo_anexos.currentData()
        if not nome:
            QMessageBox.warning(self, "Erro", "O nome da sala é obrigatório.")
            return
        try:
            execute_query(
                "INSERT INTO salas (nome, descricao, predio_id, anexo_id) VALUES (?, ?, ?, ?)",
                (nome, descricao, predio_id, anexo_id)
            )
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
            # (Opcional: atualizar combo_predios e combo_anexos baseado na linha atual)
            # Exemplo: usar um SELECT para trazer os IDs corretos e dar setCurrentIndex

    def editar_sala(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Erro", "Selecione uma sala para editar.")
            return
        sala_id = int(self.table.item(selected, 0).text())
        novo_nome = self.input_nome.text().strip()
        nova_descricao = self.input_descricao.text().strip()
        predio_id = self.combo_predios.currentData()
        anexo_id = self.combo_anexos.currentData()
        if not novo_nome:
            QMessageBox.warning(self, "Erro", "O nome da sala não pode ser vazio.")
            return
        try:
            execute_query(
                "UPDATE salas SET nome=?, descricao=?, predio_id=?, anexo_id=? WHERE id=?",
                (novo_nome, nova_descricao, predio_id, anexo_id, sala_id)
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
