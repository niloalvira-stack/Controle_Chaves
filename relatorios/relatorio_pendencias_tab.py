from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QHeaderView,
    QLabel, QProgressBar
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, QDateTime
import csv
import logging
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm

from autenticacao.helpers_autenticacao import get_db_connection

logger = logging.getLogger(__name__)


def formatar_data_br(data_str):
    """Formata data ISO para BR com fallback."""
    if not data_str:
        return "—"
    try:
        if isinstance(data_str, datetime):
            return data_str.strftime("%d/%m %H:%M")
        return datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").strftime("%d/%m %H:%M")
    except Exception:
        s = str(data_str)
        return s[:16] if len(s) > 16 else s


class PendenciasLoader(QThread):
    """Thread para carregamento assíncrono de pendências."""
    data_loaded = pyqtSignal(list, int)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = r"""
                SELECT 
                    m.chave,
                    COALESCE(u.nome, m.usuario) AS utilizador,
                    m.status,
                    m.data_retirada,
                    m.data_retorno,
                    m.id
                FROM movimentacoes m
                LEFT JOIN utilizadores u ON u.id = m.utilizador_id
                WHERE m.status = 'indisponivel'
                ORDER BY m.data_retirada ASC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            conn.close()

            total = len(rows)
            self.data_loaded.emit(rows, total)

        except Exception as e:
            logger.exception("Erro ao carregar pendências")
            self.error_occurred.emit(str(e))


class RelatorioPendenciasTab(QWidget):
    """
    Aba de relatório de pendências, usando PendenciasLoader para buscar dados.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Chave", "Utilizador", "Status", "Data Retirada", "Data Retorno"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Barra de progresso / status
        bottom = QHBoxLayout()
        self.label_status = QLabel("Pendências: 0")
        self.progress = QProgressBar()
        self.progress.setMaximum(0)
        self.progress.setVisible(False)

        btn_atualizar = QPushButton("Atualizar")
        btn_atualizar.clicked.connect(self.carregar_pendencias)

        bottom.addWidget(self.label_status)
        bottom.addStretch()
        bottom.addWidget(self.progress)
        bottom.addWidget(btn_atualizar)

        layout.addLayout(bottom)
        self.setLayout(layout)

        # Loader em thread
        self.loader = PendenciasLoader()
        self.loader.data_loaded.connect(self._atualizar_tabela)
        self.loader.error_occurred.connect(self._mostrar_erro)

        # Carrega inicial
        self.carregar_pendencias()

    def carregar_pendencias(self):
        self.progress.setVisible(True)
        self.label_status.setText("Carregando pendências...")
        self.loader.start()

    def _atualizar_tabela(self, rows, total):
        self.progress.setVisible(False)

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            chave, utilizador, status, dt_retirada, dt_retorno, mov_id = row

            self.table.setItem(i, 0, QTableWidgetItem(str(chave)))
            self.table.setItem(i, 1, QTableWidgetItem(str(utilizador)))
            self.table.setItem(i, 2, QTableWidgetItem(str(status)))
            self.table.setItem(i, 3, QTableWidgetItem(formatar_data_br(dt_retirada)))
            self.table.setItem(i, 4, QTableWidgetItem(formatar_data_br(dt_retorno)))

        self.label_status.setText(f"Pendências: {total}")

    def _mostrar_erro(self, msg):
        self.progress.setVisible(False)
        QMessageBox.critical(self, "Erro", f"Erro ao carregar pendências:\n{msg}")
