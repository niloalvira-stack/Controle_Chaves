from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDateEdit, QLabel, QHeaderView, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal
from datetime import datetime
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from autenticacao.helpers_autenticacao import get_db_connection
from utils.utils import formatar_data_br
from utils.button_style import aplicar_estilo_botao_padrao


class PendenciasLoader(QThread):
    dados_carregados = pyqtSignal(list)
    erro = pyqtSignal(str)

    def __init__(self, data_ini, data_fim):
        super().__init__()
        self.data_ini = data_ini
        self.data_fim = data_fim

    def run(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # ✅ Consulta CORRETA para o seu banco
            sql = """
                SELECT
                    cf.etiqueta,
                    COALESCE(u.nome, m.usuario) AS utilizador,
                    m.status,
                    m.data_retirada,
                    m.data_retorno,
                    m.id
                FROM movimentacoes m
                INNER JOIN chaves_fisicas cf ON cf.id = m.chave_fisica_id
                LEFT JOIN utilizadores u ON u.id = m.utilizador_id
                WHERE
                    m.status = 'indisponivel'
                    AND m.data_retirada BETWEEN %s AND %s
                ORDER BY m.data_retirada ASC
                LIMIT 1000
            """

            cursor.execute(sql, (self.data_ini, self.data_fim))
            resultados = cursor.fetchall()
            conn.close()

            self.dados_carregados.emit(resultados)
        except Exception as e:
            self.erro.emit(str(e))


class RelatorioPendenciasTab(QWidget):
    def __init__(self):
        super().__init__()
        self.loader = None
        self.init_ui()
        self.carregar_pendencias()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        layout.addWidget(QLabel("<h2>Relatório de Pendências</h2>"))

        filtro_layout = QHBoxLayout()
        filtro_layout.setSpacing(15)

        self.data_inicio = QDateEdit(calendarPopup=True)
        self.data_inicio.setDisplayFormat("dd/MM/yyyy")
        self.data_inicio.setDate(QDate.currentDate().addDays(-7))

        self.data_fim = QDateEdit(calendarPopup=True)
        self.data_fim.setDisplayFormat("dd/MM/yyyy")
        self.data_fim.setDate(QDate.currentDate())

        self.btn_carregar = QPushButton("Atualizar")
        aplicar_estilo_botao_padrao(self.btn_carregar, cor_fundo="#007bff", cor_texto="white")
        self.btn_carregar.clicked.connect(self.carregar_pendencias)

        filtro_layout.addWidget(QLabel("Data Início:"))
        filtro_layout.addWidget(self.data_inicio)
        filtro_layout.addWidget(QLabel("Data Fim:"))
        filtro_layout.addWidget(self.data_fim)
        filtro_layout.addWidget(self.btn_carregar)
        filtro_layout.addStretch()

        layout.addLayout(filtro_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Chave", "Utilizador", "Status", "Retirada", "Devolução"
        ])

        cabecalho = self.table.horizontalHeader()
        cabecalho.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cabecalho.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        cabecalho.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        export_layout = QHBoxLayout()
        self.btn_csv = QPushButton("Exportar CSV")
        self.btn_csv.clicked.connect(self.exportar_csv)
        self.btn_pdf = QPushButton("Exportar PDF")
        self.btn_pdf.clicked.connect(self.exportar_pdf)
        export_layout.addWidget(self.btn_csv)
        export_layout.addWidget(self.btn_pdf)
        export_layout.addStretch()
        layout.addLayout(export_layout)

    def carregar_pendencias(self):
        if self.loader and self.loader.isRunning():
            return

        ini = self.data_inicio.date().toString("yyyy-MM-dd") + " 00:00:00"
        fim = self.data_fim.date().toString("yyyy-MM-dd") + " 23:59:59"

        self.table.setRowCount(0)
        self.btn_carregar.setEnabled(False)
        self.btn_carregar.setText("Carregando...")

        self.loader = PendenciasLoader(ini, fim)
        self.loader.dados_carregados.connect(self.mostrar_dados)
        self.loader.erro.connect(self.mostrar_erro)
        self.loader.finished.connect(self.finalizar_carregamento)
        self.loader.start()

    def mostrar_dados(self, linhas):
        self.table.setRowCount(0)
        for idx, (chave, util, status, retirada, retorno, mid) in enumerate(linhas):
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(str(mid)))
            self.table.setItem(idx, 1, QTableWidgetItem(str(chave or "")))
            self.table.setItem(idx, 2, QTableWidgetItem(str(util or "")))
            self.table.setItem(idx, 3, QTableWidgetItem(str(status or "")))
            self.table.setItem(idx, 4, QTableWidgetItem(formatar_data_br(retirada)))
            self.table.setItem(idx, 5, QTableWidgetItem(formatar_data_br(retorno)))

    def mostrar_erro(self, msg):
        QMessageBox.critical(self, "Erro", f"Falha ao carregar pendências:\n{msg}")

    def finalizar_carregamento(self):
        self.btn_carregar.setEnabled(True)
        self.btn_carregar.setText("Atualizar")

    def obter_dados_tabela(self):
        cab = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        dados = []
        for l in range(self.table.rowCount()):
            dados.append([self.table.item(l, c).text() if self.table.item(l, c) else ""
                          for c in range(self.table.columnCount())])
        return cab, dados

    def exportar_csv(self):
        cam, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "CSV (*.csv)")
        if not cam:
            return
        cab, dados = self.obter_dados_tabela()
        with open(cam, "w", newline="", encoding="utf-8-sig") as f:
            esc = csv.writer(f, delimiter=";")
            esc.writerow(cab)
            esc.writerows(dados)
        QMessageBox.information(self, "OK", "CSV salvo!")

    def exportar_pdf(self):
        cam, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "", "PDF (*.pdf)")
        if not cam:
            return
        cab, dados = self.obter_dados_tabela()
        est = getSampleStyleSheet()
        doc = SimpleDocTemplate(cam, pagesize=landscape(A4))
        tab = Table([cab] + dados, repeatRows=1)
        tab.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ]))
        doc.build([Paragraph("Relatório de Pendências", est["Title"]), Spacer(1,10), tab])
        QMessageBox.information(self, "OK", "PDF salvo!")