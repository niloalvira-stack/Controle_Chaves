from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QMessageBox, QFileDialog, QHeaderView, QLabel, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import csv

from database_module import get_connection


class PredioDialog(QDialog):
    def __init__(self, nome="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastrar/Editar Prédio")
        self.setFixedSize(400, 120)
        layout = QFormLayout(self)
        self.nome_edit = QLineEdit(nome)
        self.nome_edit.setPlaceholderText("Digite o nome do prédio")
        layout.addRow("Nome do prédio:", self.nome_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {"nome": self.nome_edit.text().strip()}


class PrediosTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestão de Prédios")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Gestão de Prédios"))

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Cadastrar Prédio")
        self.btn_edit = QPushButton("✏️ Editar Prédio")
        self.btn_delete = QPushButton("🗑️ Excluir Prédio")
        self.btn_exportar = QPushButton("📊 Exportar CSV")
        self.btn_exportar_pdf = QPushButton("📄 Exportar PDF")

        buttons = [self.btn_add, self.btn_edit, self.btn_delete, self.btn_exportar, self.btn_exportar_pdf]
        for btn in buttons:
            btn.setFixedHeight(35)

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
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.btn_add.clicked.connect(self.cadastrar_predio)
        self.btn_edit.clicked.connect(self.editar_predio)
        self.btn_delete.clicked.connect(self.excluir_predio)
        self.btn_exportar.clicked.connect(self.exportar_csv)
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)

        # Em PostgreSQL assumo que a tabela `predios` já foi criada via migração.
        # Se quiser criar automaticamente, ajusto abaixo.
        # self.criar_tabela_predios()

        self.load_predios()

    def _get_dash_main(self):
        janela = self.parentWidget()
        while janela and janela.__class__.__name__ != "DashMain":
            janela = janela.parentWidget()
        return janela

    def criar_tabela_predios(self):
        """Cria tabela de prédios se não existir (versão PostgreSQL)."""
        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predios (
                    id SERIAL PRIMARY KEY,
                    nome TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao criar tabela prédios: {str(e)}")
        finally:
            conn.close()

    def load_predios(self):
        """Carrega prédios da base de dados (PostgreSQL)."""
        self.table.setRowCount(0)
        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM predios ORDER BY nome")
            predios = cursor.fetchall()
            print("DEBUG predios em PrediosTab:", predios)

            self.table.setRowCount(len(predios))
            for row_idx, predio in enumerate(predios):
                # predio é tupla: (id, nome)
                print("DEBUG linha", row_idx, "->", predio)
                pid, nome = predio

                if isinstance(nome, (bytes, bytearray)):
                    nome = nome.decode("utf-8")

                self.table.setItem(row_idx, 0, QTableWidgetItem(str(pid)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(nome or ""))

                for col in range(2):
                    item = self.table.item(row_idx, col)
                    if item:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar prédios: {str(e)}")
        finally:
            conn.close()

    def _show_success(self, mensagem):
        dash = self._get_dash_main()
        if dash:
            dash.show_operation_done(mensagem)

    def _validar_nome_predio(self, nome):
        nome = nome.strip()
        if not nome or len(nome) < 2:
            return False, "Nome deve ter pelo menos 2 caracteres"
        if len(nome) > 100:
            return False, "Nome muito longo (máx. 100 caracteres)"
        return True, ""

    def cadastrar_predio(self):
        dialog = PredioDialog(parent=self)
        if dialog.exec() != QDialog.Accepted:
            return

        data = dialog.get_data()
        is_valid, erro = self._validar_nome_predio(data["nome"])
        if not is_valid:
            QMessageBox.warning(self, "Erro", erro)
            return

        conn = get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO predios (nome) VALUES (%s)",
                (data["nome"],)
            )
            conn.commit()
            self.load_predios()
            self._show_success("Prédio cadastrado com sucesso!")
        except Exception as e:
            conn.rollback()
            error_msg = str(e).lower()
            if "unique" in error_msg:
                QMessageBox.warning(self, "Aviso", "Já existe um prédio com este nome!")
            else:
                QMessageBox.critical(self, "Erro", f"Erro ao cadastrar: {str(e)}")
        finally:
            conn.close()

    def editar_predio(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Aviso", "Selecione um prédio para editar!")
            return

        row = selected[0].row()
        predio_id = int(self.table.item(row, 0).text())
        nome_atual = self.table.item(row, 1).text()

        dialog = PredioDialog(nome_atual, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return

        data = dialog.get_data()
        is_valid, erro = self._validar_nome_predio(data["nome"])
        if not is_valid:
            QMessageBox.warning(self, "Erro", erro)
            return

        if data["nome"] == nome_atual:
            return

        conn = get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE predios SET nome=%s WHERE id=%s",
                (data["nome"], predio_id)
            )
            if cursor.rowcount == 0:
                raise Exception("Prédio não encontrado")
            conn.commit()
            self.load_predios()
            self._show_success("Prédio atualizado com sucesso!")
        except Exception as e:
            conn.rollback()
            error_msg = str(e).lower()
            if "unique" in error_msg:
                QMessageBox.warning(self, "Aviso", "Nome de prédio já existe!")
            else:
                QMessageBox.critical(self, "Erro", f"Erro ao editar: {str(e)}")
        finally:
            conn.close()

    def excluir_predio(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Aviso", "Selecione um prédio para excluir!")
            return

        row = selected[0].row()
        predio_id = int(self.table.item(row, 0).text())
        nome = self.table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja realmente excluir o prédio '<b>{nome}</b>'?\n\n"
            f"Esta ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        conn = get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM predios WHERE id=%s", (predio_id,))
            if cursor.rowcount == 0:
                raise Exception("Prédio não encontrado")
            conn.commit()
            self.load_predios()
            self._show_success("Prédio excluído com sucesso!")
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao excluir: {str(e)}")
        finally:
            conn.close()

    def exportar_csv(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Exportar Prédios", "predios.csv",
            "Arquivos CSV (*.csv)"
        )
        if not caminho:
            return

        try:
            with open(caminho, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Nome"])
                for row in range(self.table.rowCount()):
                    id_item = self.table.item(row, 0)
                    nome_item = self.table.item(row, 1)
                    writer.writerow([
                        id_item.text() if id_item else "",
                        nome_item.text() if nome_item else ""
                    ])
            self._show_success("CSV exportado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV: {str(e)}")

    def exportar_pdf(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Exportar Prédios", "predios.pdf",
            "Arquivos PDF (*.pdf)"
        )
        if not caminho:
            return

        try:
            doc = SimpleDocTemplate(
                caminho, pagesize=A4,
                leftMargin=36, rightMargin=36,
                topMargin=36, bottomMargin=36
            )

            story = []
            styles = getSampleStyleSheet()

            title = Paragraph("Relatório de Prédios", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))

            dados = [["ID", "Nome"]]
            for row in range(self.table.rowCount()):
                id_item = self.table.item(row, 0)
                nome_item = self.table.item(row, 1)
                dados.append([
                    id_item.text() if id_item else "",
                    nome_item.text() if nome_item else ""
                ])

            tabela = Table(dados, colWidths=[50, 500], repeatRows=1)
            estilo = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white]),
            ])
            tabela.setStyle(estilo)
            story.append(tabela)

            doc.build(story)
            self._show_success("PDF exportado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {str(e)}")
