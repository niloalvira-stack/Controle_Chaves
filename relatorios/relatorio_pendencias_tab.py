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
from database_module import DB_NAME  # usa DB_NAME central

def formatar_data_br(data_str):
    if not data_str:
        return ""
    try:
        return datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return data_str


class RelatorioPendenciasTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        btn_layout = QHBoxLayout()
        self.btn_exportar_csv = QPushButton("Exportar para CSV")
        self.btn_exportar_csv.setObjectName("btnPendenciasCsv")
        self.btn_exportar_csv.clicked.connect(self.exportar_csv)
        btn_layout.addWidget(self.btn_exportar_csv)

        self.btn_exportar_pdf = QPushButton("Exportar para PDF")
        self.btn_exportar_pdf.setObjectName("btnPendenciasPdf")
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)
        btn_layout.addWidget(self.btn_exportar_pdf)

        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Chave", "Utilizador", "Status", "Retirada", "Devolução"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.setStyleSheet("""
            QPushButton {
                padding: 10px 24px;
                min-height: 34px;
                min-width: 140px;
                border-radius: 6px;
                border: 1px solid #888;
                font-weight: 500;
            }

            QPushButton#btnPendenciasCsv {
                background-color: #2e7d32;
                color: white;
                border: 1px solid #1b5e20;
            }
            QPushButton#btnPendenciasCsv:hover {
                background-color: #388e3c;
            }
            QPushButton#btnPendenciasCsv:pressed {
                background-color: #1b5e20;
            }

            QPushButton#btnPendenciasPdf {
                background-color: #1565c0;
                color: white;
                border: 1px solid #0d47a1;
            }
            QPushButton#btnPendenciasPdf:hover {
                background-color: #1976d2;
            }
            QPushButton#btnPendenciasPdf:pressed {
                background-color: #0d47a1;
            }
        """)

        # primeira carga
        self.load_relatorio()

        # atualização automática em tempo quase real (a cada 5 segundos)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_relatorio)
        self.timer.start(5000)

    def _query_base(self):
        """
        Pendências: status 'indisponível', com JOIN utilizadores.
        COALESCE garante compatibilidade com dados antigos.
        """
        return """
            SELECT m.chave,
                   COALESCE(u.nome, m.usuario) AS utilizador,
                   m.status,
                   m.data_retirada,
                   m.data_retorno
            FROM movimentacoes m
            LEFT JOIN utilizadores u ON u.id = m.utilizador_id
            WHERE m.status = 'indisponível'
            ORDER BY m.data_retirada DESC
        """

    def load_relatorio(self):
        try:
            self.table.setRowCount(0)
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(self._query_base())
            rows = cursor.fetchall()
            conn.close()

            self.table.setRowCount(len(rows))
            for i, (chave, utilizador, status, data_ret, data_dev) in enumerate(rows):
                valores = [
                    chave or "",
                    utilizador or "",
                    status or "",
                    formatar_data_br(data_ret),
                    formatar_data_br(data_dev),
                ]
                for j, val in enumerate(valores):
                    self.table.setItem(i, j, QTableWidgetItem(str(val)))
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar relatório:\n{e}")

    def exportar_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(self._query_base())
            rows = cursor.fetchall()
            conn.close()

            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Chave", "Utilizador", "Status", "Retirada", "Devolução"])
                for chave, utilizador, status, data_ret, data_dev in rows:
                    writer.writerow([
                        chave or "",
                        utilizador or "",
                        status or "",
                        formatar_data_br(data_ret),
                        formatar_data_br(data_dev),
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
            cursor.execute(self._query_base())
            rows = cursor.fetchall()
            conn.close()

            cabecalho = ["Chave", "Utilizador", "Status", "Retirada", "Devolução"]
            tabela_dados = [cabecalho]
            for chave, utilizador, status, data_ret, data_dev in rows:
                tabela_dados.append([
                    chave or "",
                    utilizador or "",
                    status or "",
                    formatar_data_br(data_ret),
                    formatar_data_br(data_dev),
                ])

            pdf = SimpleDocTemplate(
                path, pagesize=A4, leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24
            )
            table = Table(tabela_dados, repeatRows=1)
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
            QMessageBox.information(self, "Exportação", "PDF gerado com sucesso. Ocupando toda a página!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{e}")
