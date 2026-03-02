from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QComboBox, QMessageBox, QFileDialog, QHeaderView,
    QDialogButtonBox, QLabel
)
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from database_module import get_connection  # psycopg2 com RealDictCursor


class AnexoDialog(QDialog):
    def __init__(self, predios, nome="", predio_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastro/Editar Anexo")

        layout = QFormLayout(self)

        self.nome_edit = QLineEdit(nome)

        self.combo_predio = QComboBox()
        self.combo_predio.clear()
        self.combo_predio.addItem("Nenhum", None)

        # predios é lista de RealDictRow
        print("DEBUG AnexoDialog predios recebidos:", predios)
        for row in predios:
            pid = row["id"]
            pname = row["nome"]
            self.combo_predio.addItem(str(pname), pid)

        # selecionar prédio atual (na edição)
        if predio_id is not None:
            idx = self.combo_predio.findData(predio_id)
            if idx >= 0:
                self.combo_predio.setCurrentIndex(idx)

        layout.addRow("Nome do anexo:", self.nome_edit)
        layout.addRow("Prédio:", self.combo_predio)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {
            "nome": self.nome_edit.text().strip(),
            "predio_id": self.combo_predio.currentData()
        }


class AnexosTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestão de Anexos")
        layout = QVBoxLayout(self)
        label = QLabel("Gestão de Anexos")
        layout.addWidget(label)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Cadastrar Anexo")
        self.btn_edit = QPushButton("Editar Anexo")
        self.btn_delete = QPushButton("Excluir Anexo")
        self.btn_exportar = QPushButton("Exportar CSV")
        self.btn_exportar_pdf = QPushButton("Exportar PDF")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_exportar)
        btn_layout.addWidget(self.btn_exportar_pdf)
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Prédio"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.SingleSelection)
        self.table.setColumnHidden(0, True)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.btn_add.clicked.connect(self.cadastrar_anexo)
        self.btn_edit.clicked.connect(self.editar_anexo)
        self.btn_delete.clicked.connect(self.excluir_anexo)
        self.btn_exportar.clicked.connect(self.exportar_csv)
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)

        self.load_anexos()

    def _get_dash_main(self):
        janela = self.parentWidget()
        while janela is not None and janela.__class__.__name__ != "DashMain":
            janela = janela.parentWidget()
        return janela

    def fetch_predios(self):
        try:
            conn = get_connection()
            if conn is None:
                print("DEBUG fetch_predios: conn is None")
                return []
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM predios ORDER BY nome")
            predios = cursor.fetchall()
            print("DEBUG fetch_predios rows:", predios)
            conn.close()
            return predios
        except Exception as e:
            print("DEBUG fetch_predios ERRO:", e)
            return []

    def load_anexos(self):
        self.table.setRowCount(0)
        try:
            conn = get_connection()
            if conn is None:
                return
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.id,
                       a.nome AS anexo_nome,
                       p.nome AS predio_nome
                FROM anexos a
                LEFT JOIN predios p ON a.predio_id = p.id
                ORDER BY a.nome
            """)
            rows = cursor.fetchall()
            print("DEBUG anexos em AnexosTab:", rows)

            self.table.setRowCount(len(rows))

            for row_idx, row in enumerate(rows):
                anexo_id = row["id"]
                anexo_nome = row["anexo_nome"]
                predio_nome = row["predio_nome"]

                self.table.setItem(row_idx, 0, QTableWidgetItem(str(anexo_id)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(anexo_nome)))
                self.table.setItem(
                    row_idx, 2,
                    QTableWidgetItem(str(predio_nome if predio_nome else ""))
                )

            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar anexos: {e}")

    def cadastrar_anexo(self):
        predios = self.fetch_predios()
        print("DEBUG cadastrar_anexo predios:", predios)
        dialog = AnexoDialog(predios, nome="", predio_id=None, parent=self)
        if not dialog.exec():
            return

        data = dialog.get_data()
        print("DEBUG dados retornados do dialog cadastrar:", data)
        if not data["nome"]:
            QMessageBox.warning(self, "Erro", "Nome do anexo é obrigatório.")
            return

        try:
            conn = get_connection()
            if conn is None:
                return
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO anexos (nome, predio_id) VALUES (%s, %s)",
                (data["nome"], data["predio_id"])
            )
            conn.commit()
            conn.close()
            self.load_anexos()

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Anexo cadastrado")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao cadastrar anexo: {e}")

    def editar_anexo(self):
        print("DEBUG: clicar Editar Anexo")
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um anexo para editar!")
            return
        row = selected[0].row()
        anexo_id = int(self.table.item(row, 0).text())
        nome = self.table.item(row, 1).text()
        predio_nome = self.table.item(row, 2).text()
        print("DEBUG: linha selecionada:", row, anexo_id, nome, predio_nome)

        predios = self.fetch_predios()
        print("DEBUG: predios em editar_anexo:", predios)
        predio_id = next((p["id"] for p in predios if p["nome"] == predio_nome), None)
        print("DEBUG: predio_id resolvido:", predio_id)

        dialog = AnexoDialog(predios, nome, predio_id, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            print("DEBUG dados retornados do dialog editar:", data)
            if not data["nome"]:
                QMessageBox.warning(self, "Erro", "Nome do anexo é obrigatório.")
                return
            try:
                conn = get_connection()
                if conn is None:
                    return
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE anexos SET nome = %s, predio_id = %s WHERE id = %s",
                    (data["nome"], data["predio_id"], anexo_id)
                )
                conn.commit()
                conn.close()
                self.load_anexos()

                dash = self._get_dash_main()
                if dash is not None:
                    dash.show_operation_done("Anexo atualizado")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao editar anexo: {e}")

    def excluir_anexo(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um anexo para excluir!")
            return
        row = selected[0].row()
        anexo_id = int(self.table.item(row, 0).text())
        nome = self.table.item(row, 1).text()
        reply = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja realmente excluir o anexo '{nome}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            conn = get_connection()
            if conn is None:
                return
            cursor = conn.cursor()
            cursor.execute("DELETE FROM anexos WHERE id = %s", (anexo_id,))
            conn.commit()
            conn.close()
            self.load_anexos()

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Anexo excluído")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir anexo: {e}")

    def exportar_csv(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "Arquivo CSV (*.csv)")
        if not caminho:
            return
        try:
            with open(caminho, "w", encoding="utf-8") as f:
                f.write("Nome;Prédio\n")
                for row in range(self.table.rowCount()):
                    nome = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
                    predio = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
                    f.write(f"{nome};{predio}\n")

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Exportação de anexos concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV: {e}")

    def exportar_pdf(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "", "Arquivo PDF (*.pdf)")
        if not caminho:
            return
        try:
            cabecalho = ["Nome", "Prédio"]
            dados = [cabecalho]
            for row in range(self.table.rowCount()):
                nome = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
                predio = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
                dados.append([nome, predio])
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

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Exportação PDF de anexos concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {e}")

