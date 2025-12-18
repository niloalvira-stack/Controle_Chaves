import os
import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QMessageBox, QFileDialog, QHeaderView,
    QLabel, QDialogButtonBox, QComboBox
)

# Caminho correto para o banco, relativo ao projeto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DB_NAME = os.path.join(BASE_DIR, "controle_chaves.db")


class SalaDialog(QDialog):
    def __init__(self, predios, anexos, nome="", predio_id=None, anexo_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastro/Editar Sala")
        layout = QFormLayout(self)

        self.nome_edit = QLineEdit(nome)

        self.combo_predio = QComboBox()
        self.combo_predio.addItem("Nenhum", None)
        for pid, pname in predios:
            self.combo_predio.addItem(pname, pid)
        if predio_id:
            idx = self.combo_predio.findData(predio_id)
            if idx >= 0:
                self.combo_predio.setCurrentIndex(idx)

        self.combo_anexo = QComboBox()
        self.combo_anexo.addItem("Nenhum", None)
        for aid, aname in anexos:
            self.combo_anexo.addItem(aname, aid)
        if anexo_id:
            idx = self.combo_anexo.findData(anexo_id)
            if idx >= 0:
                self.combo_anexo.setCurrentIndex(idx)

        layout.addRow("Nome da sala:", self.nome_edit)
        layout.addRow("Prédio:", self.combo_predio)
        layout.addRow("Anexo:", self.combo_anexo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_data(self):
        return {
            "nome": self.nome_edit.text().strip(),
            "predio_id": self.combo_predio.currentData(),
            "anexo_id": self.combo_anexo.currentData(),
        }


class SalasTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestão de Salas")

        layout = QVBoxLayout(self)
        label = QLabel("Gestão de Salas")
        layout.addWidget(label)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Cadastrar Sala")
        self.btn_edit = QPushButton("Editar Sala")
        self.btn_delete = QPushButton("Excluir Sala")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Prédio", "Anexo"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.SingleSelection)
        self.table.setColumnHidden(0, True)
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.btn_add.clicked.connect(self.adicionar_sala)
        self.btn_edit.clicked.connect(self.editar_sala)
        self.btn_delete.clicked.connect(self.excluir_sala)

        self.criar_tabela_salas()
        self.load_salas()

    def criar_tabela_salas(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS salas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                predio_id INTEGER,
                anexo_id INTEGER,
                status TEXT DEFAULT 'disponivel',
                FOREIGN KEY (predio_id) REFERENCES predios(id),
                FOREIGN KEY (anexo_id) REFERENCES anexos(id)
            )
        """)
        conn.commit()
        conn.close()

    def fetch_predios(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM predios ORDER BY nome")
            predios = cursor.fetchall()
            conn.close()
            return predios
        except Exception:
            return []

    def fetch_anexos(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM anexos ORDER BY nome")
            anexos = cursor.fetchall()
            conn.close()
            return anexos
        except Exception:
            return []

    def load_salas(self):
        self.table.setRowCount(0)
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, predio_id, anexo_id FROM salas ORDER BY nome")
            rows = cursor.fetchall()
            conn.close()

            prediodict = dict(self.fetch_predios())
            anexodict = dict(self.fetch_anexos())

            for row_idx, (sala_id, nome, predio_id, anexo_id) in enumerate(rows):
                predio_nome = prediodict.get(predio_id, "") if predio_id else ""
                anexo_nome = anexodict.get(anexo_id, "") if anexo_id else ""

                self.table.insertRow(row_idx)
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(sala_id)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(nome)))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(predio_nome)))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(anexo_nome)))
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar salas: {e}")

    def adicionar_sala(self):
        predios = self.fetch_predios()
        anexos = self.fetch_anexos()
        dialog = SalaDialog(predios, anexos)
        if dialog.exec():
            data = dialog.get_data()
            if not data["nome"]:
                QMessageBox.warning(self, "Erro", "Nome da sala é obrigatório.")
                return
            try:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO salas (nome, predio_id, anexo_id) VALUES (?, ?, ?)",
                    (data["nome"], data["predio_id"], data["anexo_id"])
                )
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Sucesso", "Sala cadastrada com sucesso!")
                self.load_salas()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Aviso", "Já existe uma sala com este nome!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cadastrar sala: {e}")

    def editar_sala(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione uma sala para editar!")
            return

        row = selected[0].row()
        sala_id = int(self.table.item(row, 0).text())
        nome = self.table.item(row, 1).text()
        predio_nome = self.table.item(row, 2).text()
        anexo_nome = self.table.item(row, 3).text()

        predios = self.fetch_predios()
        anexos = self.fetch_anexos()

        predio_id = next((pid for pid, pname in predios if pname == predio_nome), None)
        anexo_id = next((aid for aid, aname in anexos if aname == anexo_nome), None)

        dialog = SalaDialog(predios, anexos, nome, predio_id, anexo_id)
        if dialog.exec():
            data = dialog.get_data()
            if not data["nome"]:
                QMessageBox.warning(self, "Erro", "Nome da sala é obrigatório.")
                return
            try:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE salas SET nome=?, predio_id=?, anexo_id=? WHERE id=?",
                    (data["nome"], data["predio_id"], data["anexo_id"], sala_id)
                )
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Sucesso", "Sala atualizada com sucesso!")
                self.load_salas()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Aviso", "Já existe uma sala com este nome!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao editar sala: {e}")

    def excluir_sala(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione uma sala para excluir!")
            return

        row = selected[0].row()
        sala_id = int(self.table.item(row, 0).text())

        resposta = QMessageBox.question(
            self,
            "Confirmar exclusão",
            "Deseja excluir esta sala?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resposta != QMessageBox.Yes:
            return

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM salas WHERE id=?", (sala_id,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Sucesso", "Sala excluída!")
            self.load_salas()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir sala: {e}")
