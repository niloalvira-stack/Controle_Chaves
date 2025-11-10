from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QMessageBox, QFileDialog, QHeaderView, QLabel, QDialogButtonBox
)
import sqlite3

DB_NAME = "C:/Controle_Chaves/controle_chaves.db"

class PredioDialog(QDialog):
    def __init__(self, nome="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastrar/Editar Prédio")
        layout = QFormLayout(self)
        self.nome_edit = QLineEdit(nome)
        layout.addRow("Nome do prédio:", self.nome_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {
            "nome": self.nome_edit.text().strip()
        }

class PrediosTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestão de Prédios")
        layout = QVBoxLayout(self)
        label = QLabel("Gestão de Prédios")
        layout.addWidget(label)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Cadastrar Prédio")
        self.btn_edit = QPushButton("Editar Prédio")
        self.btn_delete = QPushButton("Excluir Prédio")
        self.btn_exportar = QPushButton("Exportar CSV")
        self.btn_exportar_pdf = QPushButton("Exportar PDF")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_exportar)
        btn_layout.addWidget(self.btn_exportar_pdf)
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ID", "Nome"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.SingleSelection)
        self.table.setColumnHidden(0, True)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.btn_add.clicked.connect(self.cadastrar_predio)
        self.btn_edit.clicked.connect(self.editar_predio)
        self.btn_delete.clicked.connect(self.excluir_predio)
        self.btn_exportar.clicked.connect(self.exportar_csv)
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)
        self.criar_tabela_predios()
        self.load_predios()

    def criar_tabela_predios(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            )
        """)
        conn.commit()
        conn.close()

    def load_predios(self):
        self.table.setRowCount(0)
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM predios ORDER BY nome")
            for row_idx, (pid, nome) in enumerate(cursor.fetchall()):
                self.table.insertRow(row_idx)
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(pid)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(nome)))
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar prédios: {e}")

    def cadastrar_predio(self):
        dialog = PredioDialog()
        if dialog.exec():
            data = dialog.get_data()
            if not data["nome"]:
                QMessageBox.warning(self, "Erro", "Nome do prédio é obrigatório.")
                return
            try:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO predios (nome) VALUES (?)",
                    (data["nome"],)
                )
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Sucesso", "Prédio cadastrado com sucesso!")
                self.load_predios()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Aviso", "Já existe um prédio com este nome!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cadastrar prédio: {e}")

    def editar_predio(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um prédio para editar!")
            return
        row = selected[0].row()
        predio_id = int(self.table.item(row, 0).text())
        nome = self.table.item(row, 1).text()
        dialog = PredioDialog(nome)
        if dialog.exec():
            data = dialog.get_data()
            if not data["nome"]:
                QMessageBox.warning(self, "Erro", "Nome do prédio é obrigatório.")
                return
            try:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE predios SET nome=? WHERE id=?",
                    (data["nome"], predio_id)
                )
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Sucesso", "Prédio atualizado com sucesso!")
                self.load_predios()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Aviso", "Nome de prédio já existe!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao editar prédio: {e}")

    def excluir_predio(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um prédio para excluir!")
            return
        row = selected[0].row()
        predio_id = int(self.table.item(row, 0).text())
        nome = self.table.item(row, 1).text()
        reply = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja realmente excluir o prédio '{nome}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM predios WHERE id=?", (predio_id,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Sucesso", "Prédio excluído!")
            self.load_predios()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir prédio: {e}")

    def exportar_csv(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "Arquivo CSV (*.csv)")
        if caminho:
            try:
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write("Nome\n")
                    for row in range(self.table.rowCount()):
                        nome = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
                        f.write(f"{nome}\n")
                QMessageBox.information(self, "Exportação", "Exportação concluída!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV: {e}")

    def exportar_pdf(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "", "Arquivo PDF (*.pdf)")
        if not caminho:
            return
        try:
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            cabecalho = ["Nome"]
            dados = [cabecalho]
            for row in range(self.table.rowCount()):
                nome = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
                dados.append([nome])
            pdf = SimpleDocTemplate(
                caminho, pagesize=A4, leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24
            )
            table = Table(dados, repeatRows=1)
            style = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ])
            table.setStyle(style)
            pdf.build([table])
            QMessageBox.information(self, "Exportação PDF", "PDF exportado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {e}")
