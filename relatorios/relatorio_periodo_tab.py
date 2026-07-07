from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QDateEdit, QLabel, QHeaderView, QApplication, QAbstractItemView
)
from PyQt6.QtCore import QDate, Qt
import csv
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from datetime import datetime
from reportlab.lib.styles import getSampleStyleSheet

from autenticacao.helpers_autenticacao import get_db_connection


def formatar_data_br(data_str):
    if not data_str:
        return ""
    try:
        if isinstance(data_str, datetime):
            return data_str.strftime("%d/%m/%Y %H:%M:%S")
        return datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(data_str)


class RelatorioPorPeriodoTab(QWidget):
    def __init__(self):
        super().__init__()
        self._rows_cache = []  # cache do último filtro
        layout = QVBoxLayout(self)

        # Filtros de período
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

        # Contador
        self.lbl_total = QLabel("0 registros")
        filtros_layout.addWidget(self.lbl_total)

        filtros_layout.addStretch()
        layout.addLayout(filtros_layout)

        # Botões exportação
        btns_layout = QHBoxLayout()
        self.btn_exportar = QPushButton("Exportar para CSV")
        self.btn_exportar.setObjectName("btnExportarPeriodoCsv")
        self.btn_exportar.clicked.connect(self.exportar_csv)
        btns_layout.addWidget(self.btn_exportar)

        self.btn_exportar_pdf = QPushButton("Exportar para PDF")
        self.btn_exportar_pdf.setObjectName("btnExportarPeriodoPdf")
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)
        btns_layout.addWidget(self.btn_exportar_pdf)

        btns_layout.addStretch()
        layout.addLayout(btns_layout)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Chave", "Utilizador", "Status", "Retirada", "Devolução"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Chave
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Utilizador
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Retirada
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Devolução
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        self.setLayout(layout)

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

    def _get_dash_main(self):
        app = QApplication.instance()
        if not app:
            return None
        for widget in app.topLevelWidgets():
            if widget.__class__.__name__ == "DashMain":
                return widget
        return None

    def _periodo(self):
        inicio = self.data_inicio.date().toString("yyyy-MM-dd") + " 00:00:00"
        fim = self.data_fim.date().toString("yyyy-MM-dd") + " 23:59:59"
        return inicio, fim

    def _query_base(self):
        # Postgres, usando BETWEEN em timestamp (ok para esse uso pontual). [web:91]
        return """
            SELECT m.id,
                   m.chave,
                   COALESCE(u.nome, m.usuario) AS utilizador,
                   m.status,
                   m.data_retirada,
                   m.data_retorno
            FROM movimentacoes m
            LEFT JOIN utilizadores u ON u.id = m.utilizador_id
            WHERE m.data_retirada BETWEEN %s AND %s
            ORDER BY m.data_retirada DESC
        """

    def _buscar_dados(self):
        inicio, fim = self._periodo()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(self._query_base(), (inicio, fim))
        rows = cursor.fetchall()
        conn.close()
        self._rows_cache = rows
        return rows

    def load_relatorio(self):
        try:
            rows = self._buscar_dados()
            self.table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                # row: [id, chave, utilizador, status, data_retirada, data_retorno]
                for j, val in enumerate(row[1:]):
                    if j in (3, 4):  # datas nas posições 3 e 4 após o ID
                        val = formatar_data_br(val)
                    item = QTableWidgetItem(str(val) if val else "")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(i, j, item)

            self.lbl_total.setText(f"{len(rows)} registros")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar relatório:\n{e}")

    def exportar_csv(self):
        if not self._rows_cache:
            self._buscar_dados()

        if not self._rows_cache:
            QMessageBox.information(self, "Informação", "Nenhum registro para exportar.")
            return

        inicio, fim = self._periodo()
        nome_sugestao = f"relatorio_periodo_{inicio[:10]}_a_{fim[:10]}.csv".replace("-", "")
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar CSV", nome_sugestao, "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["Chave", "Utilizador", "Status", "Retirada", "Devolução"])
                for row in self._rows_cache:
                    row = list(row)
                    row[4] = formatar_data_br(row[4])  # retirada
                    row[5] = formatar_data_br(row[5])  # devolução
                    writer.writerow(row[1:])  # ignora ID

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_status_message("Exportação CSV por período concluída.")
            else:
                QMessageBox.information(self, "Sucesso", "Exportação CSV concluída.")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{e}")

    def exportar_pdf(self):
        if not self._rows_cache:
            self._buscar_dados()

        if not self._rows_cache:
            QMessageBox.information(self, "Informação", "Nenhum registro para exportar.")
            return

        inicio, fim = self._periodo()
        nome_sugestao = f"relatorio_periodo_{inicio[:10]}_a_{fim[:10]}.pdf".replace("-", "")
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar PDF", nome_sugestao, "PDF Files (*.pdf)"
        )
        if not path:
            return

        try:
            cabecalho = ["Chave", "Utilizador", "Status", "Retirada", "Devolução"]
            tabela_dados = [cabecalho]
            for row in self._rows_cache:
                row = list(row)
                row[4] = formatar_data_br(row[4])
                row[5] = formatar_data_br(row[5])
                tabela_dados.append([str(x) if x else "" for x in row[1:]])  # ignora ID

            pdf = SimpleDocTemplate(
                path,
                pagesize=A4,
                leftMargin=24,
                rightMargin=24,
                topMargin=24,
                bottomMargin=24,
            )

            periodo_str = (
                f"{self.data_inicio.date().toString('dd/MM/yyyy')} a "
                f"{self.data_fim.date().toString('dd/MM/yyyy')}"
            )

            story = []
            titulo = Paragraph(f"Relatório de Movimentações por Período<br/>{periodo_str}",
                               getSampleStyleSheet()["Title"])
            story.append(titulo)
            story.append(Spacer(1, 12))

            tabela = Table(tabela_dados, repeatRows=1)
            tabela.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.whitesmoke, colors.lightgrey]),
            ]))
            story.append(tabela)

            pdf.build(story)

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_status_message("Exportação PDF por período concluída.")
            else:
                QMessageBox.information(self, "Sucesso", "Exportação PDF concluída.")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{e}")
