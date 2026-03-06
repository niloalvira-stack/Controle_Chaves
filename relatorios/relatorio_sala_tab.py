from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QComboBox, QLabel, QHeaderView, QDateEdit, QApplication
)
from PyQt5.QtCore import QDate, Qt
import csv
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from utils import montar_display_sala_variavel, show_info, show_warning
from database_module import get_connection


def formatar_data_br(data_str):
    if not data_str:
        return ""
    try:
        if isinstance(data_str, datetime):
            return data_str.strftime("%d/%m/%Y %H:%M:%S")
        return datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(data_str)


def listar_salas_para_relatorio():
    conn = get_connection()
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.nome, p.nome AS predio, a.nome AS anexo
        FROM salas s
        LEFT JOIN predios p ON s.predio_id = p.id
        LEFT JOIN anexos a ON s.anexo_id = a.id
        ORDER BY s.nome
        """
    )
    rows = cursor.fetchall()  # RealDictRow
    conn.close()

    lista = []
    for row in rows:
        nome = row["nome"]
        predio = row.get("predio")
        anexo = row.get("anexo")
        display = montar_display_sala_variavel(nome, predio, anexo)
        lista.append(display)
    return lista


class RelatorioPorSalaTab(QWidget):
    def __init__(self):
        super().__init__()
        self._rows_cache = []
        layout = QVBoxLayout(self)

        # Linha de filtros
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

        # contador
        self.lbl_total = QLabel("0 registros")
        filtro_layout.addWidget(self.lbl_total)

        filtro_layout.addStretch()
        layout.addLayout(filtro_layout)

        # Botões exportação
        btns_layout = QHBoxLayout()
        self.btn_exportar = QPushButton("Exportar para CSV")
        self.btn_exportar.setObjectName("btnExportarSalaCsv")
        self.btn_exportar.clicked.connect(self.exportar_csv)
        btns_layout.addWidget(self.btn_exportar)

        self.btn_exportar_pdf = QPushButton("Exportar para PDF")
        self.btn_exportar_pdf.setObjectName("btnExportarSalaPdf")
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
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.load_chaves()
        self.table.setRowCount(0)

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

    def _get_dash_main(self):
        app = QApplication.instance()
        if not app:
            return None
        for widget in app.topLevelWidgets():
            if widget.__class__.__name__ == "DashMain":
                return widget
        return None

    def _get_periodo(self):
        ini = self.data_inicio.date().toString("yyyy-MM-dd") + " 00:00:00"
        fim = self.data_fim.date().toString("yyyy-MM-dd") + " 23:59:59"
        return ini, fim

    def _query_base(self):
        return """
            SELECT m.chave,
                   COALESCE(u.nome, m.usuario) AS utilizador,
                   m.status,
                   m.data_retirada,
                   m.data_retorno
            FROM movimentacoes m
            LEFT JOIN utilizadores u ON u.id = m.utilizador_id
            WHERE m.chave = %s
              AND m.data_retirada >= %s
              AND m.data_retirada <= %s
            ORDER BY m.data_retirada DESC
        """

    def load_chaves(self):
        self.cb_chave.clear()
        lista = listar_salas_para_relatorio()
        self.cb_chave.addItems(lista or [""])

    def _buscar_dados(self):
        chave = self.cb_chave.currentText()
        if not chave:
            self._rows_cache = []
            return []

        data_ini, data_fim = self._get_periodo()
        conn = get_connection()
        if conn is None:
            self._rows_cache = []
            return []
        cursor = conn.cursor()
        cursor.execute(self._query_base(), (chave, data_ini, data_fim))
        rows = cursor.fetchall()  # RealDictRow
        conn.close()

        dados = []
        for row in rows:
            r = [
                row["chave"],
                row["utilizador"],
                row["status"],
                row["data_retirada"],
                row["data_retorno"],
            ]
            dados.append(r)

        self._rows_cache = dados
        return dados

    def load_relatorio(self):
        try:
            rows = self._buscar_dados()
            self.table.setRowCount(0)

            if not rows:
                self.lbl_total.setText("0 registros")
                show_info("Relatório", "Nenhuma movimentação encontrada para esta sala e período.")
                return

            self.table.setRowCount(len(rows))
            for i, (ch, utilizador, status, data_ret, data_dev) in enumerate(rows):
                valores = [
                    ch or "",
                    utilizador or "",
                    status or "",
                    formatar_data_br(data_ret),
                    formatar_data_br(data_dev),
                ]
                for j, val in enumerate(valores):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(i, j, item)

            self.lbl_total.setText(f"{len(rows)} registros")

        except Exception as e:
            show_warning("Erro", f"Erro ao carregar relatório:\n{e}")

    def exportar_csv(self):
        if not self._rows_cache:
            self._buscar_dados()

        if not self._rows_cache:
            show_info("Exportação", "Nenhuma movimentação encontrada para esta sala e período.")
            return

        chave = self.cb_chave.currentText() or "sala"
        data_ini, data_fim = self._get_periodo()
        nome_sugestao = (
            f"relatorio_sala_{chave}_{data_ini[:10]}_a_{data_fim[:10]}.csv"
        ).replace(" ", "_")
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar CSV", nome_sugestao, "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Chave", "Utilizador", "Status", "Retirada", "Devolução"])
                for row in self._rows_cache:
                    linha = list(row)
                    linha[3] = formatar_data_br(linha[3])  # retirada
                    linha[4] = formatar_data_br(linha[4])  # devolução
                    writer.writerow(linha)

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_status_message("Exportação CSV por sala concluída.")
            else:
                show_info("Sucesso", "Exportação CSV concluída.")

        except Exception as e:
            show_warning("Erro", f"Erro ao exportar CSV:\n{e}")

    def exportar_pdf(self):
        if not self._rows_cache:
            self._buscar_dados()

        if not self._rows_cache:
            show_info("Exportação", "Nenhuma movimentação encontrada para esta sala e período.")
            return

        chave = self.cb_chave.currentText() or "sala"
        data_ini, data_fim = self._get_periodo()
        nome_sugestao = (
            f"relatorio_sala_{chave}_{data_ini[:10]}_a_{data_fim[:10]}.pdf"
        ).replace(" ", "_")
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar PDF", nome_sugestao, "PDF Files (*.pdf)"
        )
        if not path:
            return

        try:
            cabecalho = ["Chave", "Utilizador", "Status", "Retirada", "Devolução"]
            tabela_dados = [cabecalho]
            for ch, utilizador, status, data_ret, data_dev in self._rows_cache:
                tabela_dados.append([
                    ch or "",
                    utilizador or "",
                    status or "",
                    formatar_data_br(data_ret),
                    formatar_data_br(data_dev),
                ])

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
            titulo = Paragraph(
                f"Relatório de Movimentações por Sala<br/>{chave}<br/>{periodo_str}",
                getSampleStyleSheet()["Title"],
            )
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
                show_info("Sucesso", "Exportação PDF por sala concluída.")
                dash.show_status_message("Exportação PDF por sala concluída.")
            else:
                show_info("Sucesso", "Exportação PDF concluída.")

        except Exception as e:
            show_warning("Erro", f"Erro ao exportar PDF:\n{e}")
