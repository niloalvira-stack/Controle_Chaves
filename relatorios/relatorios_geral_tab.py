from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QHeaderView
)
from PyQt5.QtCore import QTimer
import sqlite3
import csv
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from datetime import datetime

DB_NAME = "controle_chaves.db"


def formatar_data_br(valor):
    if not valor:
        return ""
    try:
        return datetime.strptime(valor, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(valor)


class RelatoriosGeralTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # linha de botões (CSV / PDF)
        btns_layout = QHBoxLayout()

        self.btn_exportar = QPushButton("Exportar para CSV")
        self.btn_exportar.setObjectName("btnExportarCsv")
        self.btn_exportar.clicked.connect(self.exportar_csv)
        btns_layout.addWidget(self.btn_exportar)

        self.btn_exportar_pdf = QPushButton("Exportar para PDF")
        self.btn_exportar_pdf.setObjectName("btnExportarPdf")
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)
        btns_layout.addWidget(self.btn_exportar_pdf)

        layout.addLayout(btns_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Chave", "Usuário", "Status", "Retirada", "Devolução"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setColumnHidden(0, True)  # Esconde a coluna ID na interface
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.load_relatorio()

        # atualização automática
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_relatorio)
        self.timer.start(5000)

        # estilos dos botões (seguindo padrão da aba Movimentações)
        self.setStyleSheet("""
            QPushButton {
                padding: 10px 24px;
                min-height: 34px;
                min-width: 140px;
                border-radius: 6px;
                border: 1px solid #888;
                font-weight: 500;
            }
            QPushButton#btnExportarCsv {
                background-color: #2e7d32;
                color: white;
                border: 1px solid #1b5e20;
            }
            QPushButton#btnExportarCsv:hover {
                background-color: #388e3c;
            }
            QPushButton#btnExportarCsv:pressed {
                background-color: #1b5e20;
            }

            QPushButton#btnExportarPdf {
                background-color: #1565c0;
                color: white;
                border: 1px solid #0d47a1;
            }
            QPushButton#btnExportarPdf:hover {
                background-color: #1976d2;
            }
            QPushButton#btnExportarPdf:pressed {
                background-color: #0d47a1;
            }
        """)

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
            conn.close()

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    if j in (4, 5):
                        val = formatar_data_br(val)
                    self.table.setItem(i, j, QTableWidgetItem(str(val) if val else ""))
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
                writer.writerow(["Chave", "Usuário", "Status", "Retirada", "Devolução"])
                for _id, chave, usuario, status, data_ret, data_retorn in rows:
                    writer.writerow([
                        chave,
                        usuario,
                        status,
                        formatar_data_br(data_ret),
                        formatar_data_br(data_retorn),
                    ])
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

            cabecalho = ["Chave", "Usuário", "Status", "Retirada", "Devolução"]
            dados = [cabecalho]
            for _id, chave, usuario, status, data_ret, data_retorn in rows:
                dados.append([
                    str(chave) if chave else "",
                    str(usuario) if usuario else "",
                    str(status) if status else "",
                    formatar_data_br(data_ret),
                    formatar_data_br(data_retorn),
                ])

            pdf = SimpleDocTemplate(
                path, pagesize=A4, leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24
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
            QMessageBox.information(self, "Exportação", "Relatório PDF exportado com sucesso! Ocupa toda a folha.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{e}")
