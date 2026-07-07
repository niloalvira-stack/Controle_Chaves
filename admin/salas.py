from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from utils.button_style import aplicar_estilo_botao_padrao

import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ_PROJETO))

from database_init import get_db_connection


class SalasTab(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.init_ui()
        self.carregar_dados()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(15)

        layout_botoes = QHBoxLayout()
        layout_botoes.setSpacing(12)
        layout_botoes.setContentsMargins(0, 0, 0, 15)

        self.btn_cadastrar = QPushButton("Cadastrar Sala")
        self.btn_editar = QPushButton("Editar Sala")
        self.btn_excluir = QPushButton("Excluir Sala")
        self.btn_csv = QPushButton("Exportar CSV")
        self.btn_pdf = QPushButton("Exportar PDF")

        aplicar_estilo_botao_padrao(self.btn_cadastrar, "#0d6efd", "#ffffff")
        aplicar_estilo_botao_padrao(self.btn_editar, "#fd7e14", "#ffffff")
        aplicar_estilo_botao_padrao(self.btn_excluir, "#dc3545", "#ffffff")
        aplicar_estilo_botao_padrao(self.btn_csv, "#198754", "#ffffff")
        aplicar_estilo_botao_padrao(self.btn_pdf, "#6c757d", "#ffffff")

        def definir_icone(botao, caminho):
            icone = QIcon(caminho)
            if not icone.isNull():
                botao.setIcon(icone)
                botao.setIconSize(QSize(16, 16))

        definir_icone(self.btn_cadastrar, "recursos/icones/adicionar.png")
        definir_icone(self.btn_editar, "recursos/icones/editar.png")
        definir_icone(self.btn_excluir, "recursos/icones/excluir.png")
        definir_icone(self.btn_csv, "recursos/icones/csv.png")
        definir_icone(self.btn_pdf, "recursos/icones/pdf.png")

        layout_botoes.addWidget(self.btn_cadastrar)
        layout_botoes.addWidget(self.btn_editar)
        layout_botoes.addWidget(self.btn_excluir)
        layout_botoes.addStretch()
        layout_botoes.addWidget(self.btn_csv)
