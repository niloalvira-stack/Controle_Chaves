from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QDateEdit, QLabel, QHeaderView
)
from PyQt5.QtCore import QDate
import os
import sqlite3
import csv
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime

from database_module import DB_NAME


def formatar_data_br(data_str):
    if not data_str:
        return ""
    try:
        return datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return data_str


class RelatorioPorPeriodoTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        filtros_layout = QHBoxLayout()
        filtros_layout.addWidget(QLabel("Data Início:"))
        self.data_inicio = QDateEdit()
        self.data_inicio.setCalendarPopup(True)
        self.data_inicio.setDisplayFormat("dd/MM/yyyy")
        self.data_inicio.setDate(QDate.currentDate())
        filtros_layout.addWidget(self.data_inicio)

        filtros_layout.addWidget(QLabel("Data Fim:"))
        self.data_fim = QDateEdit()
        self.data_fim.setCalendarPopup(True)
        self.data_fim.setDisplayFormat("dd/MM/yyyy")
        self.data_fim.setDate(QDate.currentDate())
        filtros_layout.addWidget(self.data_fim)

        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_filtrar.setObjectName("btnFiltrarPeriodo")
        self.btn_filtrar.clicked.connect(self.load_relatorio)
        filtros_layout.addWidget(self.btn_filtrar)
        layout.addLayout(filtros_layout)

        btns_layout = QHBoxLayout()
        self.btn_exportar = QPushButton("Exportar para CSV")
        self.btn_exportar.setObjectName("btnExportarPeriodoCsv")
        self.btn_exportar.clicked.connect(self.exportar_csv)
        btns_layout.addWidget(self.btn_exportar)

        self.btn_exportar_pdf = QPushButton("Exportar para PDF")
        self.btn_exportar_pdf.setObjectName("btnExportarPeriodoPdf")
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)
        btns_layout.addWidget(self.btn_exportar_pdf)
        layout.addLayout(btns_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Chave", "Utilizador", "Status", "Retirada", "Devolução"]
        )
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

            QPushButton#btnFiltrarPeriodo {
                background-color: #f9a825;
                color: #333333;
                border: 1px solid #f57f17;
            }
            QPushButton#btnFiltrarPeriodo:hover {
                background-color: #fbc02d;
            }
            QPushButton#btnFiltrarPeriodo:pressed {
                background-color: #f57f17;
            }

            QPushButton#btnExportarPeriodoCsv {
                background-color: #2e7d32;
                color: white;
                border: 1px solid #1b5e20;
            }
            QPushButton#btnExportarPeriodoCsv:hover {
                background-color: #388e3c;
            }
            QPushButton#btnExportarPeriodoCsv:pressed {
                background-color: #1b5e20;
            }

            QPushButton#btnExportarPeriodoPdf {
                background-color: #1565c0;
                color: white;
                border: 1px solid #0d47a1;
            }
            QPushButton#btnExportarPeriodoPdf:hover {
                background-color: #1976d2;
            }
            QPushButton#btnExportarPeriodoPdf:pressed {
                background-color: #0d47a1;
            }
        """)

        self.load_relatorio()

    def _periodo(self):
        inicio = self.data_inicio.date().toString("yyyy-MM-dd") + " 00:00:00"
        fim = self.data_fim.date().toString("yyyy-MM-dd") + " 23:59:59"
        return inicio, fim

    def _query_base(self):
        """
        Query base por período, com JOIN utilizadores e compatibilidade com dados antigos.
        """
        return """
            SELECT m.id,
                   m.chave,
                   COALESCE(u.nome, m.usuario) AS utilizador,
                   m.status,
                   m.data_retirada,
                   m.data_retorno
            FROM movimentacoes m
            LEFT JOIN utilizadores u ON u.id = m.utilizador_id
            WHERE m.data_retirada >= ? AND m.data_retirada <= ?
            ORDER BY m.data_retirada DESC
        """

    def load_relatorio(self):
        inicio, fim = self._periodo()
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(self._query_base(), (inicio, fim))
            rows = cursor.fetchall()
            conn.close()

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                # row: [id, chave, utilizador, status, data_retirada, data_retorno]
                for j, val in enumerate(row[1:]):
                    if j in [3, 4]:  # datas nas posições 3 e 4 após o ID
                        val = formatar_data_br(val)
                    self.table.setItem(i, j, QTableWidgetItem(str(val) if val else ""))
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar relatório:\n{e}")

    def exportar_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        inicio, fim = self._periodo()
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(self._query_base(), (inicio, fim))
            rows = cursor.fetchall()
            conn.close()

            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Chave", "Utilizador", "Status", "Retirada", "Devolução"])
                for row in rows:
                    row = list(row)
                    row[4] = formatar_data_br(row[4])  # retirada
                    row[5] = formatar_data_br(row[5])  # devolução
                    writer.writerow(row[1:])  # ignora ID
            QMessageBox.information(self, "Sucesso", "Relatório exportado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{e}")

    def exportar_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        inicio, fim = self._periodo()
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(self._query_base(), (inicio, fim))
            rows = cursor.fetchall()
            conn.close()

            cabecalho = ["Chave", "Utilizador", "Status", "Retirada", "Devolução"]
            tabela_dados = [cabecalho]
            for row in rows:
                row = list(row)
                row[4] = formatar_data_br(row[4])
                row[5] = formatar_data_br(row[5])
                tabela_dados.append([str(x) if x else "" for x in row[1:]])  # ignora ID

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
            QMessageBox.information(self, "Exportação", "PDF gerado com sucesso! Ocupa toda a página.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{e}")
