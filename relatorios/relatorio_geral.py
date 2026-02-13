from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QHeaderView, QApplication
)
from PyQt5.QtCore import Qt
import os
import sqlite3
import csv
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# Caminho do banco relativo à raiz do projeto (mantendo padrão do projeto)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DB_NAME = os.path.join(BASE_DIR, "controle_chaves.db")


class RelatorioGeralTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Botões
        btns_layout = QVBoxLayout()
        self.btn_exportar = QPushButton("Exportar para CSV")
        self.btn_exportar.clicked.connect(self.exportar_csv)
        btns_layout.addWidget(self.btn_exportar)

        self.btn_exportar_pdf = QPushButton("Exportar para PDF")
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)
        btns_layout.addWidget(self.btn_exportar_pdf)

        layout.addLayout(btns_layout)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Chave", "Utilizador", "Status", "Retirada", "Devolução"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.load_relatorio()

    def _get_dash_main(self):
        """
        Recupera a janela principal (DashMain) para usar show_operation_done.
        """
        app = QApplication.instance()
        if not app:
            return None
        for widget in app.topLevelWidgets():
            # Evita import circular conferindo pelo nome da classe
            if widget.__class__.__name__ == "DashMain":
                return widget
        return None

    def _query_base(self):
        """
        Query base usando JOIN com utilizadores.
        COALESCE garante compatibilidade com dados antigos (coluna usuario).
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
            ORDER BY m.data_retirada DESC
        """

    def load_relatorio(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(self._query_base())
            rows = cursor.fetchall()
            conn.close()

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    item = QTableWidgetItem(str(val) if val is not None else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(i, j, item)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar relatório:\n{e}")

    def exportar_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar CSV", "", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(self._query_base())
            rows = cursor.fetchall()
            conn.close()

            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["ID", "Chave", "Utilizador", "Status", "Retirada", "Devolução"]
                )
                writer.writerows(rows)

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Exportação CSV concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{e}")

    def exportar_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar PDF", "", "PDF Files (*.pdf)"
        )
        if not path:
            return
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(self._query_base())
            rows = cursor.fetchall()
            conn.close()

            cabecalho = ["ID", "Chave", "Utilizador", "Status", "Retirada", "Devolução"]
            dados = [cabecalho] + [
                [str(x) if x is not None else "" for x in row] for row in rows
            ]

            pdf = SimpleDocTemplate(
                path,
                pagesize=A4,
                leftMargin=24,
                rightMargin=24,
                topMargin=24,
                bottomMargin=24,
            )
            table = Table(dados, repeatRows=1)
            style = TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
            table.setStyle(style)
            pdf.build([table])

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Exportação PDF concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{e}")


class RelatoriosTab:
    pass
