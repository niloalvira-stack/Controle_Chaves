from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QHeaderView,
    QProgressDialog, QLabel, QComboBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
import csv
import logging
from datetime import datetime
from utils.ui_colors import aplicar_cor_status_item_generico

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm

from autenticacao.helpers_autenticacao import get_db_connection
import config  # para cores

logger = logging.getLogger(__name__)

ALERTA_HORAS = 6


def aplicar_cor_status_item_relatorio(item, status, retirada_val, now):
    status = (status or "").strip()

    try:
        if status == "disponível":
            cor_hex = config.COLOR_STATUS_DISPONIVEL

        elif status == "indisponível":
            atraso = False
            if retirada_val:
                try:
                    if isinstance(retirada_val, datetime):
                        retirada_dt = retirada_val
                    else:
                        retirada_dt = datetime.strptime(str(retirada_val), "%Y-%m-%d %H:%M:%S")
                    diff_horas = (now - retirada_dt).total_seconds() / 3600
                    atraso = diff_horas >= ALERTA_HORAS
                except Exception:
                    atraso = False

            cor_hex = config.COLOR_STATUS_ATRASO if atraso else config.COLOR_STATUS_INDISPONIVEL
        else:
            return

        item.setBackground(QBrush(QColor(cor_hex)))
    except Exception:
        pass


class DatabaseLoader(QThread):
    """Thread para carregar dados sem travar a UI."""
    data_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, query, params=None):
        super().__init__()
        self.query = query
        self.params = params or []

    def run(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(self.query, self.params)
            rows = cursor.fetchall()
            conn.close()
            self.data_loaded.emit(rows)
        except Exception as e:
            self.error_occurred.emit(str(e))


class RelatorioGeralTab(QWidget):
    def __init__(self):
        super().__init__()
        self.dados = []
        self.loader = None
        self.setup_ui()
        self.setup_connections()
        self.load_relatorio()

    def setup_ui(self):
        self.setWindowTitle("Relatório Geral - Controle de Chaves")
        self.resize(1000, 600)

        layout = QVBoxLayout(self)

        filtros_layout = QHBoxLayout()
        filtros_layout.addWidget(QLabel("Período:"))

        self.combo_periodo = QComboBox()
        self.combo_periodo.addItems(["Todos", "Hoje", "Esta Semana", "Este Mês"])
        self.combo_periodo.currentTextChanged.connect(self._atualizar_query)
        filtros_layout.addWidget(self.combo_periodo)

        filtros_layout.addStretch()

        self.label_total = QLabel(f"Total: {len(self.dados)} registros")
        filtros_layout.addWidget(self.label_total)

        layout.addLayout(filtros_layout)

        btns_layout = QHBoxLayout()
        self.btn_atualizar = QPushButton("🔄 Atualizar")
        self.btn_csv = QPushButton("📊 CSV")
        self.btn_pdf = QPushButton("📄 PDF")

        for btn in (self.btn_atualizar, self.btn_csv, self.btn_pdf):
            btns_layout.addWidget(btn)
        btns_layout.addStretch()
        layout.addLayout(btns_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Chave", "Utilizador", "Status", "Retirada", "Devolução"
        ])
        self._configurar_tabela()
        layout.addWidget(self.table)

        self.setLayout(layout)

    def _configurar_tabela(self):
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)

    def setup_connections(self):
        self.btn_atualizar.clicked.connect(self.load_relatorio)
        self.btn_csv.clicked.connect(self.exportar_csv)
        self.btn_pdf.clicked.connect(self.exportar_pdf)

    def _get_dash_main(self):
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                if hasattr(widget, '__class__') and widget.__class__.__name__ == "DashMain":
                    return widget
        return None

    def _query_base(self, periodo="TODOS"):
        base_query = """
            SELECT m.id,
                   m.chave,
                   COALESCE(u.nome, m.usuario) AS utilizador,
                   m.status,
                   m.data_retirada,
                   m.data_retorno
            FROM movimentacoes m
            LEFT JOIN utilizadores u ON u.id = m.utilizador_id
            WHERE 1=1
        """

        params = []

        periodo = periodo.upper()
        if periodo == "HOJE":
            base_query += " AND DATE(m.data_retirada) = CURRENT_DATE"
        elif periodo == "ESTA_SEMANA":
            base_query += """
                AND DATE(m.data_retirada) >= date_trunc('week', CURRENT_DATE)::date
                AND DATE(m.data_retirada) <= CURRENT_DATE
            """
        elif periodo == "ESTE_MES":
            base_query += """
                AND date_trunc('month', m.data_retirada) = date_trunc('month', CURRENT_DATE)
            """

        base_query += " ORDER BY m.data_retirada DESC"
        return base_query, params

    def _atualizar_query(self):
        pass

    def load_relatorio(self):
        if self.loader and self.loader.isRunning():
            self.loader.terminate()

        periodo = self.combo_periodo.currentText().upper().replace(" ", "_")
        query, params = self._query_base(periodo)

        self.loader = DatabaseLoader(query, params)
        self.loader.data_loaded.connect(self._preencher_tabela)
        self.loader.error_occurred.connect(self._tratar_erro_load)
        self.loader.start()

        self.btn_atualizar.setText("⏳ Carregando...")

    def _preencher_tabela(self, rows):
        self.dados = rows
        self.table.setRowCount(len(rows))
        now = datetime.now()

        for i, row in enumerate(rows):
            # row: [id, chave, utilizador, status, data_retirada, data_retorno]
            for j, val in enumerate(row):
                display_val = val
                if j in (4, 5) and isinstance(val, datetime):
                    display_val = val.strftime("%d/%m/%Y %H:%M:%S")

                item = QTableWidgetItem(str(display_val) if display_val is not None else "")
                item.setTextAlignment(Qt.AlignCenter)

                if j == 3:
                    status_str = str(val) if val is not None else ""
                    retirada_val = row[4]
                    retorno_val = row[5]
                    aplicar_cor_status_item_generico(item, status_str, retirada_val, retorno_val, now)

                self.table.setItem(i, j, item)

        self.btn_atualizar.setText("✅ Atualizado")
        self._atualizar_contador()

    def _atualizar_contador(self):
        self.label_total.setText(f"Total: {len(self.dados)} registros")

    def _tratar_erro_load(self, erro):
        QMessageBox.critical(self, "Erro", f"Erro ao carregar relatório:\n{erro}")
        self.btn_atualizar.setText("❌ Erro")
        logger.error(f"Erro carregamento relatório: {erro}")

    def _get_dados_query(self):
        periodo = self.combo_periodo.currentText().upper().replace(" ", "_")
        query, params = self._query_base(periodo)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            dados = cursor.fetchall()
            conn.close()
            return dados
        except Exception as e:
            logger.error(f"Erro exportação: {e}")
            raise

    def exportar_csv(self):
        dados = self._get_dados_query()
        if not dados:
            QMessageBox.information(self, "Info", "Não há dados para exportar.")
            return

        periodo = self.combo_periodo.currentText().upper().replace(" ", "_")
        data_str = datetime.now().strftime("%Y%m%d_%H%M")
        default_name = f"relatorio_geral_{periodo.lower()}_{data_str}.csv"

        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar CSV", default_name, "Arquivos CSV (*.csv)"
        )
        if not caminho:
            return

        try:
            with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["ID", "Chave", "Utilizador", "Status", "Retirada", "Devolução"])
                for row in dados:
                    row = list(row)
                    for idx in (4, 5):
                        if isinstance(row[idx], datetime):
                            row[idx] = row[idx].strftime("%d/%m/%Y %H:%M:%S")
                    writer.writerow(row)

            dash = self._get_dash_main()
            if dash:
                dash.show_status_message("CSV do relatório geral exportado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao exportar CSV: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{e}")

    def exportar_pdf(self):
        dados = self._get_dados_query()
        if not dados:
            QMessageBox.information(self, "Info", "Não há dados para exportar.")
            return

        periodo = self.combo_periodo.currentText()
        data_str = datetime.now().strftime("%Y%m%d_%H%M")
        default_name = f"relatorio_geral_{periodo.lower().replace(' ', '_')}_{data_str}.pdf"

        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar PDF", default_name, "Arquivos PDF (*.pdf)"
        )
        if not caminho:
            return

        try:
            doc = SimpleDocTemplate(
                caminho,
                pagesize=A4,
                leftMargin=20 * mm,
                rightMargin=20 * mm,
                topMargin=20 * mm,
                bottomMargin=20 * mm,
            )

            styles = getSampleStyleSheet()
            story = []

            titulo = Paragraph("Relatório Geral de Movimentações", styles["Title"])
            story.append(titulo)
            story.append(Spacer(1, 6))

            subtitulo = Paragraph(
                f"Período: {periodo} &nbsp;&nbsp;&nbsp; Gerado em: "
                f"{datetime.now().strftime('%d/%m/%Y %H:%M')}",
                styles["Normal"],
            )
            story.append(subtitulo)
            story.append(Spacer(1, 12))

            tabela_dados = [["ID", "Chave", "Utilizador", "Status", "Retirada", "Devolução"]]
            for row in dados:
                row = list(row)
                for idx in (4, 5):
                    if isinstance(row[idx], datetime):
                        row[idx] = row[idx].strftime("%d/%m/%Y %H:%M:%S")
                    elif row[idx] is None:
                        row[idx] = ""
                tabela_dados.append([str(row[0]), row[1], row[2], row[3], row[4], row[5]])

            tabela = Table(tabela_dados, repeatRows=1)
            estilo = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ])
            tabela.setStyle(estilo)

            story.append(tabela)
            doc.build(story)

            dash = self._get_dash_main()
            if dash:
                dash.show_status_message("PDF do relatório geral exportado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao exportar PDF: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{e}")
