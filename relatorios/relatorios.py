from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QHeaderView
)
import sqlite3
import csv
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

DB_NAME = "controle_chaves.db"

class RelatoriosTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        btns_layout = QVBoxLayout()
        self.btn_exportar = QPushButton("Exportar para CSV")
        self.btn_exportar.clicked.connect(self.exportar_csv)
        btns_layout.addWidget(self.btn_exportar)

        self.btn_exportar_pdf = QPushButton("Exportar para PDF")
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)
        btns_layout.addWidget(self.btn_exportar_pdf)

        layout.addLayout(btns_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Chave", "Usuário", "Status", "Retirada", "Devolução"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.load_relatorio()

    def load_relatorio(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, chave, usuario, status, data_retirada, data_retorno
                FROM movimentacoes
                ORDER BY data_retirada DESC
            """)
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    self.table.setItem(i, j, QTableWidgetItem(str(val) if val else ""))
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar relatório:\n{e}")

    def exportar_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, chave, usuario, status, data_retirada, data_retorno
                FROM movimentacoes
                ORDER BY data_retirada DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Chave", "Usuário", "Status", "Retirada", "Devolução"])
                writer.writerows(rows)
            QMessageBox.information(self, "Sucesso", "Relatório exportado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{e}")

    def exportar_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, chave, usuario, status, data_retirada, data_retorno
                FROM movimentacoes
                ORDER BY data_retirada DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            cabecalho = ["ID", "Chave", "Usuário", "Status", "Retirada", "Devolução"]
            dados = [cabecalho] + [[str(x) if x else "" for x in row] for row in rows]
            pdf = SimpleDocTemplate(
                path, pagesize=A4, leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24
            )
            table = Table(dados, repeatRows=1)
            style = TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
                ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE", (0,0), (-1,-1), 9),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("TOPPADDING", (0,0), (-1,-1), 2),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ])
            table.setStyle(style)
            pdf.build([table])
            QMessageBox.information(self, "Exportação", "Relatório PDF exportado com sucesso! Ocupa toda a folha.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{e}")
