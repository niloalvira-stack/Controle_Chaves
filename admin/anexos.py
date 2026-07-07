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


class AnexosTab(QWidget):
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

        self.btn_cadastrar = QPushButton("Cadastrar Anexo")
        self.btn_editar = QPushButton("Editar Anexo")
        self.btn_excluir = QPushButton("Excluir Anexo")
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
        layout_botoes.addWidget(self.btn_pdf)

        layout_principal.addLayout(layout_botoes)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Prédio"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self.table.setColumnHidden(0, True)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)

        layout_principal.addWidget(self.table)

        self.btn_cadastrar.clicked.connect(self.abrir_cadastro)
        self.btn_editar.clicked.connect(self.abrir_edicao)
        self.btn_excluir.clicked.connect(self.confirmar_exclusao)
        self.btn_csv.clicked.connect(self.exportar_csv)
        self.btn_pdf.clicked.connect(self.exportar_pdf)

    def carregar_dados(self):
        self.table.setRowCount(0)
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT a.id, a.nome, COALESCE(p.nome, '')
                FROM anexos a
                LEFT JOIN predios p ON p.id = a.predio_id
                ORDER BY a.nome
            """)
            lista = cur.fetchall()

            for linha, anexo in enumerate(lista):
                self.table.insertRow(linha)
                self.table.setItem(linha, 0, QTableWidgetItem(str(anexo[0])))
                self.table.setItem(linha, 1, QTableWidgetItem(str(anexo[1])))
                self.table.setItem(linha, 2, QTableWidgetItem(str(anexo[2])))

        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível carregar anexos:\n{str(e)}")
        finally:
            if conn:
                conn.close()

    def abrir_cadastro(self):
        QMessageBox.information(self, "Cadastro", "Cadastro de anexo")

    def abrir_edicao(self):
        linha = self.table.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um anexo!")
            return

    def confirmar_exclusao(self):
        linha = self.table.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um anexo!")
            return

    def exportar_csv(self):
        QMessageBox.information(self, "Exportar", "Exportação para CSV")

    def exportar_pdf(self):
        QMessageBox.information(self, "Exportar", "Exportação para PDF")