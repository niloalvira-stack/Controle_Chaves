import logging
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QLabel,
    QProgressBar, QAbstractItemView, QDateEdit
)

from autenticacao.helpers_autenticacao import get_db_connection
from utils.button_style import aplicar_estilo_botao_padrao

logger = logging.getLogger(__name__)


def formatar_data_br(data_str):
    if not data_str:
        return "—"
    try:
        if isinstance(data_str, datetime):
            return data_str.strftime("%d/%m/%Y %H:%M")
        return datetime.strptime(str(data_str), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
    except Exception:
        s = str(data_str)
        return s[:16] if len(s) > 16 else s


class PendenciasLoader(QThread):
    data_loaded = pyqtSignal(list, int)
    error_occurred = pyqtSignal(str)

    def __init__(self, data_inicio=None, data_fim=None, parent=None):
        super().__init__(parent)
        self.data_inicio = data_inicio
        self.data_fim = data_fim

    def run(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = """
                SELECT
                    m.chave,
                    COALESCE(u.nome, m.usuario) AS utilizador,
                    m.status,
                    m.data_retirada,
                    m.data_retorno,
                    m.id
                FROM movimentacoes m
                LEFT JOIN utilizadores u ON u.id = m.utilizador_id
                WHERE
                    m.status = 'indisponivel'
                    AND m.data_retirada BETWEEN %s AND %s
                ORDER BY m.data_retirada ASC
                LIMIT 1000
            """

            inicio = self.data_inicio or (datetime.now() - timedelta(days=90))
            fim = self.data_fim or datetime.now()

            cursor.execute(sql, (inicio, fim))
            rows = cursor.fetchall()
            self.data_loaded.emit(rows, len(rows))

        except Exception as e:
            logger.exception("Erro ao carregar pendências")
            self.error_occurred.emit(str(e))
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass


class RelatorioPendenciasTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.loader = None
        self.carregando = False

        self._setup_ui()
        self.carregar_pendencias()

    def _icone(self, nome):
        caminhos = {
            "refresh": "icons/refresh.png",
        }
        caminho = caminhos.get(nome, "")
        return QIcon(caminho) if caminho else QIcon()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Período:"))

        self.data_inicio = QDateEdit()
        self.data_inicio.setDisplayFormat("dd/MM/yyyy")
        self.data_inicio.setCalendarPopup(True)
        self.data_inicio.setDate((datetime.now() - timedelta(days=90)).date())

        self.data_fim = QDateEdit()
        self.data_fim.setDisplayFormat("dd/MM/yyyy")
        self.data_fim.setCalendarPopup(True)
        self.data_fim.setDate(datetime.now().date())

        filtro_layout.addWidget(QLabel("De:"))
        filtro_layout.addWidget(self.data_inicio)
        filtro_layout.addWidget(QLabel("Até:"))
        filtro_layout.addWidget(self.data_fim)
        filtro_layout.addStretch()

        layout.addLayout(filtro_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Chave", "Utilizador", "Status", "Data Retirada", "Data Retorno"
        ])
        self._configurar_tabela()
        layout.addWidget(self.table)

        bottom = QHBoxLayout()

        self.label_status = QLabel("Pendências: 0")

        self.progress = QProgressBar()
        self.progress.setMaximum(0)
        self.progress.setVisible(False)
        self.progress.setFixedWidth(160)

        self.btn_atualizar = QPushButton("Atualizar")
        self.btn_atualizar.setIcon(self._icone("refresh"))
        self.btn_atualizar.setIconSize(QSize(18, 18))
        aplicar_estilo_botao_padrao(self.btn_atualizar, "#0d6efd", "#ffffff")
        self.btn_atualizar.clicked.connect(self.carregar_pendencias)

        bottom.addWidget(self.label_status)
        bottom.addStretch()
        bottom.addWidget(self.progress)
        bottom.addWidget(self.btn_atualizar)

        layout.addLayout(bottom)

    def _configurar_tabela(self):
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)

    def _set_carregando(self, ativo: bool):
        self.carregando = ativo
        self.progress.setVisible(ativo)
        self.btn_atualizar.setEnabled(not ativo)
        if ativo:
            self.label_status.setText("Carregando pendências...")

    def carregar_pendencias(self):
        if self.carregando:
            return

        inicio = datetime.combine(self.data_inicio.date().toPyDate(), datetime.min.time())
        fim = datetime.combine(self.data_fim.date().toPyDate(), datetime.max.time())

        if inicio > fim:
            QMessageBox.warning(self, "Período inválido", "A data inicial não pode ser maior que a data final.")
            return

        self._set_carregando(True)

        self.loader = PendenciasLoader(data_inicio=inicio, data_fim=fim, parent=self)
        self.loader.data_loaded.connect(self._atualizar_tabela)
        self.loader.error_occurred.connect(self._mostrar_erro)
        self.loader.finished.connect(self._finalizar_carregamento)
        self.loader.finished.connect(self.loader.deleteLater)
        self.loader.start()

    def _finalizar_carregamento(self):
        self.carregando = False
        self.progress.setVisible(False)
        self.btn_atualizar.setEnabled(True)
        self.loader = None

    def _atualizar_tabela(self, rows, total):
        self.table.setUpdatesEnabled(False)
        self.table.clearContents()
        self.table.setRowCount(len(rows))

        for i, row in enumerate(rows):
            chave, utilizador, status, dt_retirada, dt_retorno, mov_id = row

            item0 = QTableWidgetItem(str(chave or "—"))
            item1 = QTableWidgetItem(str(utilizador or "—"))
            item2 = QTableWidgetItem(str(status or "—"))
            item3 = QTableWidgetItem(formatar_data_br(dt_retirada))
            item4 = QTableWidgetItem(formatar_data_br(dt_retorno))

            for item in (item0, item1, item2, item3, item4):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(i, 0, item0)
            self.table.setItem(i, 1, item1)
            self.table.setItem(i, 2, item2)
            self.table.setItem(i, 3, item3)
            self.table.setItem(i, 4, item4)

        self.table.setUpdatesEnabled(True)
        self.label_status.setText(f"Pendências: {total}")

    def _mostrar_erro(self, msg):
        self.label_status.setText("Erro ao carregar pendências")
        QMessageBox.critical(self, "Erro", f"Erro ao carregar pendências:\n{msg}")