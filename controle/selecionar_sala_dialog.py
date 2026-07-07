from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QHeaderView, QMessageBox
)
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtCore import Qt
import config
from autenticacao.helpers_autenticacao import get_db_connection
from utils.utils import montar_display_sala_por_id


class SelecionarSalaDialog(QDialog):
    def __init__(self, parent=None, is_admin=False):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Sala / Chave")
        self.resize(950, 550)
        self.is_admin = is_admin
        self.sala_id_selecionada = None
        self.sala_display_selecionada = None

        self.init_ui()
        self.carregar_salas()
        self.aplicar_estilo_padrao()

    def aplicar_estilo_padrao(self):
        """Aplica o mesmo estilo usado no restante do sistema"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #ffffff;
                font-family: Segoe UI, Roboto, sans-serif;
                font-size: 10pt;
            }}
            QLineEdit {{
                padding: 6px 8px;
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                min-height: 28px;
                font-size: 10pt;
            }}
            QPushButton {{
                padding: 8px 16px;
                min-height: 32px;
                border-radius: 5px;
                border: 1px solid #bdbdbd;
                font-weight: 500;
                font-size: 10pt;
            }}
            QPushButton#btnOk {{
                background-color: {config.COLOR_BTN_VERDE};
                color: {config.COLOR_BTN_TEXTO};
                border: 1px solid #2e7d32;
            }}
            QPushButton#btnOk:hover {{
                background-color: #43a047;
            }}
            QPushButton#btnOk:pressed {{
                background-color: #2e7d32;
            }}
            QPushButton#btnCancelar {{
                background-color: #eeeeee;
                color: #333333;
                border: 1px solid #bdbdbd;
            }}
            QPushButton#btnCancelar:hover {{
                background-color: #e0e0e0;
            }}
            QPushButton#btnCancelar:pressed {{
                background-color: #bdbdbd;
            }}
            QPushButton#btnFiltrar {{
                background-color: {config.COLOR_BTN_LARANJA};
                color: {config.COLOR_BTN_TEXTO_ESCURO};
                border: 1px solid #f57c00;
            }}
            QPushButton#btnFiltrar:hover {{
                background-color: #ff9800;
            }}
            QPushButton#btnFiltrar:pressed {{
                background-color: #f57c00;
            }}
            QTableWidget {{
                gridline-color: #e0e0e0;
                selection-background-color: #bbdefb;
                selection-color: black;
                border: 1px solid #e0e0e0;
                font-size: 10pt;
            }}
            QHeaderView::section {{
                background-color: #f5f5f5;
                padding: 6px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
            }}
        """)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Área de filtro
        filtro_layout = QHBoxLayout()
        self.input_filtro = QLineEdit()
        self.input_filtro.setPlaceholderText("Filtrar por sala, descrição, prédio / anexo / status")
        self.input_filtro.textChanged.connect(self.filtrar_tabela)

        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_filtrar.setObjectName("btnFiltrar")
        self.btn_filtrar.clicked.connect(self.carregar_salas)

        filtro_layout.addWidget(self.input_filtro)
        filtro_layout.addWidget(self.btn_filtrar)
        layout.addLayout(filtro_layout)

        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels([
            "Sala", "Descrição", "Prédio", "Anexo", "Status"
        ])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setSelectionMode(QTableWidget.SingleSelection)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.doubleClicked.connect(self.selecionar_e_fechar)
        layout.addWidget(self.tabela)

        # Botões inferiores
        botoes_layout = QHBoxLayout()
        botoes_layout.addStretch()

        self.btn_ok = QPushButton("OK")
        self.btn_ok.setObjectName("btnOk")
        self.btn_ok.clicked.connect(self.selecionar_e_fechar)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("btnCancelar")
        self.btn_cancelar.clicked.connect(self.reject)

        botoes_layout.addWidget(self.btn_ok)
        botoes_layout.addWidget(self.btn_cancelar)
        layout.addLayout(botoes_layout)

    def carregar_salas(self):
        self.tabela.setRowCount(0)
        filtro = self.input_filtro.text().strip().lower()

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT id, numero_sala, descricao, predio, anexo, status
                FROM salas
                WHERE 1=1
            """
            params = []

            if filtro:
                query += """
                    AND (
                        LOWER(numero_sala) LIKE %s
                        OR LOWER(descricao) LIKE %s
                        OR LOWER(predio) LIKE %s
                        OR LOWER(anexo) LIKE %s
                        OR LOWER(status) LIKE %s
                    )
                """
                params = [f"%{filtro}%"] * 5

            if not self.is_admin:
                query += " AND status = 'disponivel'"

            query += " ORDER BY numero_sala, descricao"
            cursor.execute(query, params)
            linhas = cursor.fetchall()

            for linha_idx, (sala_id, numero, desc, predio, anexo, status) in enumerate(linhas):
                self.tabela.insertRow(linha_idx)

                self.tabela.setItem(linha_idx, 0, QTableWidgetItem(str(numero)))
                self.tabela.setItem(linha_idx, 1, QTableWidgetItem(str(desc or "")))
                self.tabela.setItem(linha_idx, 2, QTableWidgetItem(str(predio or "")))
                self.tabela.setItem(linha_idx, 3, QTableWidgetItem(str(anexo or "")))

                item_status = QTableWidgetItem(str(status or ""))
                if status == "disponivel":
                    item_status.setBackground(QBrush(QColor(config.COLOR_STATUS_DISPONIVEL)))
                elif status == "indisponivel":
                    item_status.setBackground(QBrush(QColor(config.COLOR_STATUS_INDISPONIVEL)))
                self.tabela.setItem(linha_idx, 4, item_status)

                # Armazena o ID da sala na linha
                self.tabela.item(linha_idx, 0).setData(Qt.ItemDataRole.UserRole, sala_id)

        finally:
            conn.close()

    def filtrar_tabela(self):
        self.carregar_salas()

    def selecionar_e_fechar(self):
        linhas_selecionadas = self.tabela.selectionModel().selectedRows()
        if not linhas_selecionadas:
            QMessageBox.information(self, "Aviso", "Selecione uma sala primeiro.")
            return

        linha = linhas_selecionadas[0].row()
        self.sala_id_selecionada = self.tabela.item(linha, 0).data(Qt.ItemDataRole.UserRole)
        self.sala_display_selecionada = montar_display_sala_por_id(self.sala_id_selecionada)

        self.accept()