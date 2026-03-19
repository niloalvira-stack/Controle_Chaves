from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QMessageBox, QFileDialog, QHeaderView,
    QLabel, QDialogButtonBox, QComboBox
)
from PyQt5.QtCore import Qt

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

import csv

from database_module import get_connection  # usa o banco oficial
print("DEBUG: carregando admin/salas.py - classe SalasTab nova")


class SalaDialog(QDialog):
    def __init__(self, predios, anexos, nome="", descricao="", predio_id=None, anexo_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastro/Editar Sala")
        layout = QFormLayout(self)

        self.nome_edit = QLineEdit(nome)
        self.descricao_edit = QLineEdit(descricao)

        self.combo_predio = QComboBox()
        self.combo_predio.addItem("Nenhum", None)
        # predios: lista de tuplas (id, nome)
        for row in predios:
            pid, pname = row
            if isinstance(pname, (bytes, bytearray)):
                pname = pname.decode("utf-8")
            self.combo_predio.addItem(pname, pid)
        if predio_id:
            idx = self.combo_predio.findData(predio_id)
            if idx >= 0:
                self.combo_predio.setCurrentIndex(idx)

        self.combo_anexo = QComboBox()
        self.combo_anexo.addItem("Nenhum", None)
        # anexos: lista de tuplas (id, nome)
        for row in anexos:
            aid, aname = row
            if isinstance(aname, (bytes, bytearray)):
                aname = aname.decode("utf-8")
            self.combo_anexo.addItem(aname, aid)
        if anexo_id:
            idx = self.combo_anexo.findData(anexo_id)
            if idx >= 0:
                self.combo_anexo.setCurrentIndex(idx)

        layout.addRow("Nome da sala:", self.nome_edit)
        layout.addRow("Descrição:", self.descricao_edit)
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
            "descricao": self.descricao_edit.text().strip(),
            "predio_id": self.combo_predio.currentData(),
            "anexo_id": self.combo_anexo.currentData(),
        }


class SalasTab(QWidget):
    def __init__(self):
        super().__init__()
        print("DEBUG: SalasTab.__init__ (nova) chamada")
        self.setWindowTitle("Gestão de Salas")

        layout = QVBoxLayout(self)
        label = QLabel("Gestão de Salas")
        layout.addWidget(label)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Cadastrar Sala")
        self.btn_edit = QPushButton("Editar Sala")
        self.btn_delete = QPushButton("Excluir Sala")
        self.btn_exportar = QPushButton("Exportar CSV")
        self.btn_exportar_pdf = QPushButton("Exportar PDF")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_exportar)
        btn_layout.addWidget(self.btn_exportar_pdf)
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Descrição", "Prédio", "Anexo", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.SingleSelection)
        self.table.setColumnHidden(0, True)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.btn_add.clicked.connect(self.adicionar_sala)
        self.btn_edit.clicked.connect(self.editar_sala)
        self.btn_delete.clicked.connect(self.excluir_sala)
        self.btn_exportar.clicked.connect(self.exportar_csv)
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)

        self.load_salas()

    def _get_dash_main(self):
        janela = self.parentWidget()
        while janela is not None and janela.__class__.__name__ != "DashMain":
            janela = janela.parentWidget()
        return janela

    def _show_success(self, mensagem):
        dash = self._get_dash_main()
        if dash:
            dash.show_operation_done(mensagem)

    def fetch_predios(self):
        try:
            conn = get_connection()
            if conn is None:
                return []
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM predios ORDER BY nome")
            predios = cursor.fetchall()
            conn.close()
            return predios
        except Exception:
            return []

    def fetch_anexos(self):
        try:
            conn = get_connection()
            if conn is None:
                return []
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
            conn = get_connection()
            if conn is None:
                return
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id,
                       s.nome,
                       s.descricao,
                       p.nome AS predio_nome,
                       a.nome AS anexo_nome,
                       s.status
                FROM salas s
                LEFT JOIN predios p ON s.predio_id = p.id
                LEFT JOIN anexos a ON s.anexo_id = a.id
                ORDER BY s.nome
            """)
            salas = cursor.fetchall()
            print("DEBUG salas em SalasTab:", salas)

            self.table.setRowCount(len(salas))
            for row_idx, row in enumerate(salas):
                # (id, nome, descricao, predio_nome, anexo_nome, status)
                sid, nome, descricao, predio_nome, anexo_nome, status = row

                for var_name, value in [
                    ("nome", nome),
                    ("descricao", descricao),
                    ("predio_nome", predio_nome),
                    ("anexo_nome", anexo_nome),
                    ("status", status),
                ]:
                    if isinstance(value, (bytes, bytearray)):
                        locals()[var_name] = value.decode("utf-8")

                if isinstance(nome, (bytes, bytearray)):
                    nome = nome.decode("utf-8")
                if isinstance(descricao, (bytes, bytearray)):
                    descricao = descricao.decode("utf-8")
                if isinstance(predio_nome, (bytes, bytearray)):
                    predio_nome = predio_nome.decode("utf-8")
                if isinstance(anexo_nome, (bytes, bytearray)):
                    anexo_nome = anexo_nome.decode("utf-8")
                if isinstance(status, (bytes, bytearray)):
                    status = status.decode("utf-8")

                self.table.setItem(row_idx, 0, QTableWidgetItem(str(sid)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(nome or ""))
                self.table.setItem(row_idx, 2, QTableWidgetItem(descricao or ""))
                self.table.setItem(row_idx, 3, QTableWidgetItem(predio_nome or ""))
                self.table.setItem(row_idx, 4, QTableWidgetItem(anexo_nome or ""))
                self.table.setItem(row_idx, 5, QTableWidgetItem(status or ""))

                for col in range(6):
                    item = self.table.item(row_idx, col)
                    if item:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar salas: {e}")

    def _validar_nome_sala(self, nome):
        nome = nome.strip()
        return bool(nome)

    def adicionar_sala(self):
        predios = self.fetch_predios()
        anexos = self.fetch_anexos()

        dialog = SalaDialog(predios, anexos, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            nome = data["nome"]

            if not self._validar_nome_sala(nome):
                QMessageBox.warning(self, "Atenção", "Nome da sala é obrigatório.")
                return

            try:
                conn = get_connection()
                if conn is None:
                    return
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO salas (nome, descricao, predio_id, anexo_id, status)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (nome, data["descricao"], data["predio_id"], data["anexo_id"], "disponivel"),
                )
                conn.commit()
                conn.close()
                self.load_salas()
                self._show_success("Sala cadastrada com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cadastrar sala: {e}")

    def editar_sala(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma sala para editar.")
            return

        sid_item = self.table.item(row, 0)
        nome_item = self.table.item(row, 1)
        desc_item = self.table.item(row, 2)
        predio_item = self.table.item(row, 3)
        anexo_item = self.table.item(row, 4)

        if not sid_item:
            QMessageBox.warning(self, "Erro", "Registro inválido.")
            return

        sala_id = int(sid_item.text())
        nome_atual = nome_item.text() if nome_item else ""
        descricao_atual = desc_item.text() if desc_item else ""
        predio_nome_atual = predio_item.text() if predio_item else ""
        anexo_nome_atual = anexo_item.text() if anexo_item else ""

        predios = self.fetch_predios()
        anexos = self.fetch_anexos()

        predio_id_atual = None
        for row_p in predios:
            pid, pname = row_p
            if isinstance(pname, (bytes, bytearray)):
                pname = pname.decode("utf-8")
            if pname == predio_nome_atual:
                predio_id_atual = pid
                break

        anexo_id_atual = None
        for row_a in anexos:
            aid, aname = row_a
            if isinstance(aname, (bytes, bytearray)):
                aname = aname.decode("utf-8")
            if aname == anexo_nome_atual:
                anexo_id_atual = aid
                break

        dialog = SalaDialog(
            predios, anexos,
            nome=nome_atual,
            descricao=descricao_atual,
            predio_id=predio_id_atual,
            anexo_id=anexo_id_atual,
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            nome_novo = data["nome"]

            if not self._validar_nome_sala(nome_novo):
                QMessageBox.warning(self, "Atenção", "Nome da sala é obrigatório.")
                return

            try:
                conn = get_connection()
                if conn is None:
                    return
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE salas
                    SET nome = %s, descricao = %s, predio_id = %s, anexo_id = %s
                    WHERE id = %s
                    """,
                    (nome_novo, data["descricao"], data["predio_id"], data["anexo_id"], sala_id),
                )
                conn.commit()
                conn.close()
                self.load_salas()
                self._show_success("Sala editada com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao editar sala: {e}")

    def excluir_sala(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma sala para excluir.")
            return

        sid_item = self.table.item(row, 0)
        nome_item = self.table.item(row, 1)
        if not sid_item:
            QMessageBox.warning(self, "Erro", "Registro inválido.")
            return

        sala_id = int(sid_item.text())
        nome = nome_item.text() if nome_item else ""

        resp = QMessageBox.question(
            self,  # QWidget pai
            "Confirmação",
            f"Tem certeza que deseja excluir a sala '{nome}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if resp == QMessageBox.Yes:
            try:
                conn = get_connection()
                if conn is None:
                    return
                cursor = conn.cursor()
                cursor.execute("DELETE FROM salas WHERE id = %s", (sala_id,))
                conn.commit()
                conn.close()
                self.load_salas()
                self._show_success("Sala excluída com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir sala: {e}")

    def exportar_csv(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar salas para CSV", "salas.csv", "CSV (*.csv)"
        )
        if not filename:
            return

        try:
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["ID", "Nome", "Descrição", "Prédio", "Anexo", "Status"])
                for row in range(self.table.rowCount()):
                    rowdata = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        rowdata.append(item.text() if item else "")
                    writer.writerow(rowdata)
            self._show_success("Salas exportadas para CSV com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV: {e}")

    def exportar_pdf(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar salas para PDF", "salas.pdf", "PDF (*.pdf)"
        )
        if not filename:
            return

        try:
            doc = SimpleDocTemplate(filename, pagesize=A4)
            data = [["ID", "Nome", "Descrição", "Prédio", "Anexo", "Status"]]
            for row in range(self.table.rowCount()):
                rowdata = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    rowdata.append(item.text() if item else "")
                data.append(rowdata)

            table = Table(data)
            style = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ])
            table.setStyle(style)
            elements = [table]
            doc.build(elements)
            self._show_success("Salas exportadas para PDF com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {e}")
