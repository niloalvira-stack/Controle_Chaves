from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QComboBox, QLabel, QHeaderView, QDateEdit
)
from PyQt5.QtCore import QDate
import sqlite3
import csv
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from utils import montar_display_sala_variavel, show_info, show_warning

DB_NAME = "controle_chaves.db"


def formatar_data_br(data_str):
    if not data_str:
        return ""
    try:
        return datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return data_str


def listar_salas_para_relatorio():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.nome, p.nome, a.nome
        FROM salas s
        LEFT JOIN predios p ON s.predio_id = p.id
        LEFT JOIN anexos a ON s.anexo_id = a.id
        ORDER BY s.nome
    """)
    lista = []
    for nome, predio, anexo in cursor.fetchall():
        display = montar_display_sala_variavel(nome, predio, anexo)
        lista.append(display)
    conn.close()
    return lista


class RelatorioPorSalaTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Filtros: sala + período
        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Sala:"))
        self.cb_chave = QComboBox()
        filtro_layout.addWidget(self.cb_chave)

        filtro_layout.addWidget(QLabel("Início:"))
        self.data_inicio = QDateEdit(calendarPopup=True)
        self.data_inicio.setDisplayFormat("dd/MM/yyyy")
        self.data_inicio.setDate(QDate.currentDate())
        filtro_layout.addWidget(self.data_inicio)

        filtro_layout.addWidget(QLabel("Fim:"))
        self.data_fim = QDateEdit(calendarPopup=True)
        self.data_fim.setDisplayFormat("dd/MM/yyyy")
        self.data_fim.setDate(QDate.currentDate())
        filtro_layout.addWidget(self.data_fim)

        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_filtrar.setObjectName("btnFiltrarSala")
        self.btn_filtrar.clicked.connect(self.load_relatorio)
        filtro_layout.addWidget(self.btn_filtrar)

        layout.addLayout(filtro_layout)

        btns_layout = QHBoxLayout()
        self.btn_exportar = QPushButton("Exportar para CSV")
        self.btn_exportar.setObjectName("btnExportarSalaCsv")
        self.btn_exportar.clicked.connect(self.exportar_csv)
        btns_layout.addWidget(self.btn_exportar)

        self.btn_exportar_pdf = QPushButton("Exportar para PDF")
        self.btn_exportar_pdf.setObjectName("btnExportarSalaPdf")
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)
        btns_layout.addWidget(self.btn_exportar_pdf)

        layout.addLayout(btns_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Chave", "Usuário", "Status", "Retirada", "Devolução"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.load_chaves()
        self.table.setRowCount(0)  # começa vazio

        # estilos dos botões (mesmo padrão das outras abas)
        self.setStyleSheet("""
            QPushButton {
                padding: 10px 24px;
                min-height: 34px;
                min-width: 140px;
                border-radius: 6px;
                border: 1px solid #888;
                font-weight: 500;
            }

            QPushButton#btnFiltrarSala {
                background-color: #f9a825;
                color: #333333;
                border: 1px solid #f57f17;
            }
            QPushButton#btnFiltrarSala:hover {
                background-color: #fbc02d;
            }
            QPushButton#btnFiltrarSala:pressed {
                background-color: #f57f17;
            }

            QPushButton#btnExportarSalaCsv {
                background-color: #2e7d32;
                color: white;
                border: 1px solid #1b5e20;
            }
            QPushButton#btnExportarSalaCsv:hover {
                background-color: #388e3c;
            }
            QPushButton#btnExportarSalaCsv:pressed {
                background-color: #1b5e20;
            }

            QPushButton#btnExportarSalaPdf {
                background-color: #1565c0;
                color: white;
                border: 1px solid #0d47a1;
            }
            QPushButton#btnExportarSalaPdf:hover {
                background-color: #1976d2;
            }
            QPushButton#btnExportarSalaPdf:pressed {
                background-color: #0d47a1;
            }
        """)

    def _get_periodo(self):
        ini = self.data_inicio.date().toString("yyyy-MM-dd") + " 00:00:00"
        fim = self.data_fim.date().toString("yyyy-MM-dd") + " 23:59:59"
        return ini, fim

    def load_chaves(self):
        self.cb_chave.clear()
        lista = listar_salas_para_relatorio()
        self.cb_chave.addItems(lista or [""])

    def load_relatorio(self):
        chave = self.cb_chave.currentText()
        if not chave:
            self.table.setRowCount(0)
            return
        data_ini, data_fim = self._get_periodo()
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chave, usuario, status, data_retirada, data_retorno
                FROM movimentacoes
                WHERE chave = ?
                  AND data_retirada >= ?
                  AND data_retirada <= ?
                ORDER BY data_retirada DESC
            """, (chave, data_ini, data_fim))
            rows = cursor.fetchall()
            conn.close()

            self.table.setRowCount(0)
            if not rows:
                show_info("Relatório", "Nenhuma movimentação encontrada para esta sala e período.")
                return

            self.table.setRowCount(len(rows))
            for i, (ch, usuario, status, data_ret, data_dev) in enumerate(rows):
                valores = [
                    ch or "",
                    usuario or "",
                    status or "",
                    formatar_data_br(data_ret),
                    formatar_data_br(data_dev),
                ]
                for j, val in enumerate(valores):
                    self.table.setItem(i, j, QTableWidgetItem(str(val)))
        except Exception as e:
            show_warning("Erro", f"Erro ao carregar relatório:\n{e}")

    def exportar_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        chave = self.cb_chave.currentText()
        if not chave:
            return
        data_ini, data_fim = self._get_periodo()
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chave, usuario, status, data_retirada, data_retorno
                FROM movimentacoes
                WHERE chave = ?
                  AND data_retirada >= ?
                  AND data_retirada <= ?
                ORDER BY data_retirada DESC
            """, (chave, data_ini, data_fim))
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                show_info("Exportação", "Nenhuma movimentação encontrada para esta sala e período.")
                return

            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Chave", "Usuário", "Status", "Retirada", "Devolução"])
                for ch, usuario, status, data_ret, data_dev in rows:
                    writer.writerow([
                        ch or "",
                        usuario or "",
                        status or "",
                        formatar_data_br(data_ret),
                        formatar_data_br(data_dev),
                    ])
            show_info("Sucesso", "Relatório exportado com sucesso!")
        except Exception as e:
            show_warning("Erro", f"Erro ao exportar CSV:\n{e}")

    def exportar_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        chave = self.cb_chave.currentText()
        if not chave:
            return
        data_ini, data_fim = self._get_periodo()
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chave, usuario, status, data_retirada, data_retorno
                FROM movimentacoes
                WHERE chave = ?
                  AND data_retirada >= ?
                  AND data_retirada <= ?
                ORDER BY data_retirada DESC
            """, (chave, data_ini, data_fim))
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                show_info("Exportação", "Nenhuma movimentação encontrada para esta sala e período.")
                return

            cabecalho = ["Chave", "Usuário", "Status", "Retirada", "Devolução"]
            dados = [cabecalho]
            for ch, usuario, status, data_ret, data_dev in rows:
                dados.append([
                    ch or "",
                    usuario or "",
                    status or "",
                    formatar_data_br(data_ret),
                    formatar_data_br(data_dev),
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
            show_info("Exportação", "Relatório PDF exportado com sucesso!")
        except Exception as e:
            show_warning("Erro", f"Erro ao exportar PDF:\n{e}")
