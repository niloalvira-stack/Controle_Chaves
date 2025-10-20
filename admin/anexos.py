from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QMessageBox
)
from database_module import execute_query

class AnexosTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Prédio"])
        self.layout.addWidget(self.table)
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Nome do anexo")
        self.combo_predios = QComboBox()
        self.combo_predios.addItem("Nenhum", None)
        self.load_predios_combobox()
        self.btn_add = QPushButton("Adicionar")
        self.btn_edit = QPushButton("Alterar")
        self.btn_delete = QPushButton("Excluir")
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.input_nome)
        h_layout.addWidget(self.combo_predios)
        h_layout.addWidget(self.btn_add)
        h_layout.addWidget(self.btn_edit)
        h_layout.addWidget(self.btn_delete)
        self.layout.addLayout(h_layout)
        self.btn_add.clicked.connect(self.add_anexo)
        self.btn_edit.clicked.connect(self.edit_anexo)
        self.btn_delete.clicked.connect(self.delete_anexo)
        self.load_anexos()

    def load_predios_combobox(self):
        self.combo_predios.clear()
        self.combo_predios.addItem("Nenhum", None)
        predios = execute_query("SELECT id, nome FROM predios ORDER BY nome ASC", (), fetchall=True)
        for predio in predios:
            self.combo_predios.addItem(predio["nome"], predio["id"])

    def load_anexos(self):
        self.table.setRowCount(0)
        anexos = execute_query(
            "SELECT a.id, a.nome, p.nome as predio_nome FROM anexos a LEFT JOIN predios p ON a.predio_id = p.id ORDER BY a.id DESC",
            (), fetchall=True
        )
        for row_idx, anexo in enumerate(anexos):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(anexo["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(anexo["nome"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(anexo["predio_nome"] or "Nenhum"))

    def add_anexo(self):
        nome = self.input_nome.text().strip()
        predio_id = self.combo_predios.currentData()
        if not nome:
            QMessageBox.warning(self, "Aviso", "Digite o nome do anexo!")
            return
        try:
            result = execute_query("INSERT INTO anexos (nome, predio_id) VALUES (?, ?)", (nome, predio_id))
            success = result is not None
            if success:
                QMessageBox.information(self, "Sucesso", f"Anexo '{nome}' adicionado!")
                self.load_anexos()
                self.input_nome.clear()
            else:
                QMessageBox.critical(self, "Erro", "Falha ao adicionar anexo.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao adicionar anexo: {str(e)}")

    def edit_anexo(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um anexo para alterar!")
            return
        anexo_id = int(self.table.item(selected, 0).text())
        novo_nome = self.input_nome.text().strip()
        predio_id = self.combo_predios.currentData()
        if not novo_nome:
            QMessageBox.warning(self, "Aviso", "Digite o novo nome do anexo!")
            return
        try:
            result = execute_query(
                "UPDATE anexos SET nome=?, predio_id=? WHERE id=?",
                (novo_nome, predio_id, anexo_id)
            )
            success = result is not None
            if success:
                QMessageBox.information(self, "Sucesso", "Anexo alterado com sucesso!")
                self.load_anexos()
                self.input_nome.clear()
            else:
                QMessageBox.critical(self, "Erro", "Falha ao alterar anexo.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao alterar anexo: {str(e)}")

    def delete_anexo(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um anexo para excluir!")
            return
        anexo_id = int(self.table.item(selected, 0).text())
        try:
            result = execute_query("DELETE FROM anexos WHERE id=?", (anexo_id,))
            success = result is not None
            if success:
                QMessageBox.information(self, "Sucesso", "Anexo excluído com sucesso!")
                self.load_anexos()
            else:
                QMessageBox.critical(self, "Erro", "Falha ao excluir anexo.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao excluir anexo: {str(e)}")
