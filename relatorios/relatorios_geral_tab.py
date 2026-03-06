from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QHeaderView, QApplication
)
from PyQt5.QtCore import QTimer, Qt
import csv
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from datetime import datetime
from reportlab.lib.styles import getSampleStyleSheet

from database_module import get_connection


def formatar_data_br(valor):
    if not valor:
        return ""
    try:
        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y %H:%M:%S")
        return datetime.strptime(valor, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(valor)


class RelatoriosGeralTab(QWidget):
    def __init__(self):
        super().__init__()
        self._rows_cache = []

        layout = QVBoxLayout(self)

        # Botões
        btns_layout = QHBoxLayout()

        self.btn_exportar = QPushButton("Exportar para CSV")
        self.btn_exportar.setObjectName("btnExportarCsv")
        self.btn_exportar.clicked.connect(self.exportar_csv)
        btns_layout.addWidget(self.btn_exportar)

        self.btn_exportar_pdf = QPushButton("Exportar para PDF")
        self.btn_exportar_pdf.setObjectName("btnExportarPdf")
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)
        btns_layout.addWidget(self.btn_exportar_pdf)

        btns_layout.addStretch()
        layout.addLayout(btns_layout)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Chave", "Utilizador", "Status", "Retirada", "Devolução"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setColumnHidden(0, True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.load_relatorio()

        # Auto-refresh
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_relatorio)
        self.timer.start(10000)

        # Estilo
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

    def _get_dash_main(self):
        app = QApplication.instance()
        if not app:
            return None
        for widget in app.topLevelWidgets():
            if widget.__class__.__name__ == "DashMain":
                return widget
        return None

    def _query_base(self):
        return """
            SELECT m.id,
                   m.chave,
                   COALESCE(u.nome, m.usuario) AS utilizador,
                   m.status,
                   m.data_retirada,
                   m.data_retorno
            FROM movimentacoes m
            LEFT JOIN utilizadores u ON u.id = m.utilizador_id
            ORDER BY m.data_retirada DESC
        """

    def _buscar_dados(self):
        conn = get_connection()
        if conn is None:
            self._rows_cache = []
            return []
        cursor = conn.cursor()
        cursor.execute(self._query_base())
        rows = cursor.fetchall()  # RealDictRow
        conn.close()

        dados = []
        for row in rows:
            dados.append([
                row["id"],
                row["chave"],
                row["utilizador"],
                row["status"],
                row["data_retirada"],
                row["data_retorno"],
            ])

        self._rows_cache = dados
        return dados

    def load_relatorio(self):
        try:
            rows = self._buscar_dados()
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    if j in (4, 5):
                        val = formatar_data_br(val)
                    item = QTableWidgetItem(str(val) if val else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(i, j, item)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar relatório:\n{e}")

    def exportar_csv(self):
        if not self._rows_cache:
            self._buscar_dados()

        if not self._rows_cache:
            QMessageBox.information(self, "Exportar CSV", "Não há dados para exportar.")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M")
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar CSV", f"relatorio_geral_{ts}.csv", "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["Chave", "Utilizador", "Status", "Retirada", "Devolução"])
                for _id, chave, utilizador, status, data_ret, data_retorn in self._rows_cache:
                    writer.writerow([
                        chave or "",
                        utilizador or "",
                        status or "",
                        formatar_data_br(data_ret),
                        formatar_data_br(data_retorn),
                    ])

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_status_message("Exportação CSV geral concluída.")
            else:
                QMessageBox.information(self, "Exportar CSV", "Exportação concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{e}")

    def exportar_pdf(self):
        if not self._rows_cache:
            self._buscar_dados()

        if not self._rows_cache:
            QMessageBox.information(self, "Exportar PDF", "Não há dados para exportar.")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M")
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar PDF", f"relatorio_geral_{ts}.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return

        try:
            cabecalho = ["Chave", "Utilizador", "Status", "Retirada", "Devolução"]
            dados = [cabecalho]
            for _id, chave, utilizador, status, data_ret, data_retorn in self._rows_cache:
                dados.append([
                    str(chave) if chave else "",
                    str(utilizador) if utilizador else "",
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

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_status_message("Exportação PDF geral concluída.")
            else:
                QMessageBox.information(self, "Exportar PDF", "Exportação concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{e}")
