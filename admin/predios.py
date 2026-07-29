from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QAbstractItemView,
    QFileDialog, QInputDialog
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize, Qt

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from utils.button_style import aplicar_estilo_botao_padrao

import csv
import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ_PROJETO))

from database_init import get_db_connection


class PrediosTab(QWidget):
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

        self.btn_cadastrar = QPushButton("Cadastrar Prédio")
        self.btn_editar = QPushButton("Editar Prédio")
        self.btn_excluir = QPushButton("Excluir Prédio")
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
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ID", "Nome"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

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

    def _get_dash_main(self):
        janela = self.parentWidget()
        while janela is not None and janela.__class__.__name__ != "DashMain":
            janela = janela.parentWidget()
        return janela

    def _show_success(self, mensagem):
        dash = self._get_dash_main()
        if dash:
            dash.show_operation_done(mensagem)
        else:
            QMessageBox.information(self, "Sucesso", mensagem)

    def _obter_predio_id_da_linha(self, linha):
        nome_item = self.table.item(linha, 1)
        if not nome_item:
            return None
        return nome_item.data(Qt.ItemDataRole.UserRole)

    def _validar_nome(self, nome):
        return bool(nome and nome.strip())

    def carregar_dados(self):
        self.table.setRowCount(0)
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM predios ORDER BY nome")
            lista = cur.fetchall()

            for linha, predio in enumerate(lista):
                pid = predio[0]
                nome = predio[1]

                self.table.insertRow(linha)

                item_id = QTableWidgetItem(str(pid))
                item_nome = QTableWidgetItem(str(nome or ""))
                item_nome.setData(Qt.ItemDataRole.UserRole, pid)

                self.table.setItem(linha, 0, item_id)
                self.table.setItem(linha, 1, item_nome)

        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível carregar prédios:\n{str(e)}")
        finally:
            if conn:
                conn.close()

    def abrir_cadastro(self):
        nome, ok = QInputDialog.getText(self, "Cadastrar Prédio", "Nome do prédio:")
        if not ok:
            return

        nome = nome.strip()
        if not self._validar_nome(nome):
            QMessageBox.warning(self, "Aviso", "O nome do prédio é obrigatório.")
            return

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO predios (nome) VALUES (%s)", (nome,))
            conn.commit()
            self.carregar_dados()
            self._show_success("Prédio cadastrado com sucesso!")
        except Exception as e:
            if conn:
                conn.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao cadastrar prédio:\n{str(e)}")
        finally:
            if conn:
                conn.close()

    def abrir_edicao(self):
        linha = self.table.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um prédio na tabela!")
            return

        predio_id = self._obter_predio_id_da_linha(linha)
        nome_item = self.table.item(linha, 1)

        if predio_id is None or not nome_item:
            QMessageBox.warning(self, "Erro", "Registro inválido.")
            return

        nome_atual = nome_item.text()

        novo_nome, ok = QInputDialog.getText(
            self, "Editar Prédio", "Nome do prédio:", text=nome_atual
        )
        if not ok:
            return

        novo_nome = novo_nome.strip()
        if not self._validar_nome(novo_nome):
            QMessageBox.warning(self, "Aviso", "O nome do prédio é obrigatório.")
            return

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE predios SET nome = %s WHERE id = %s",
                (novo_nome, predio_id)
            )
            conn.commit()
            self.carregar_dados()
            self._show_success("Prédio editado com sucesso!")
        except Exception as e:
            if conn:
                conn.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao editar prédio:\n{str(e)}")
        finally:
            if conn:
                conn.close()

    def confirmar_exclusao(self):
        linha = self.table.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um prédio!")
            return

        predio_id = self._obter_predio_id_da_linha(linha)
        nome_item = self.table.item(linha, 1)

        if predio_id is None or not nome_item:
            QMessageBox.warning(self, "Erro", "Registro inválido.")
            return

        nome = nome_item.text()

        resposta = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja excluir o prédio '{nome}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if resposta != QMessageBox.StandardButton.Yes:
            return

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM predios WHERE id = %s", (predio_id,))
            conn.commit()
            self.carregar_dados()
            self._show_success("Prédio excluído com sucesso!")
        except Exception as e:
            if conn:
                conn.rollback()
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao excluir prédio:\n{str(e)}"
            )
        finally:
            if conn:
                conn.close()

    def exportar_csv(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar prédios para CSV", "predios.csv", "CSV (*.csv)"
        )
        if not filename:
            return

        try:
            colunas_visiveis = [
                col for col in range(self.table.columnCount())
                if not self.table.isColumnHidden(col)
            ]

            headers = [
                self.table.horizontalHeaderItem(col).text()
                for col in colunas_visiveis
            ]

            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)

                for row in range(self.table.rowCount()):
                    rowdata = []
                    for col in colunas_visiveis:
                        item = self.table.item(row, col)
                        rowdata.append(item.text() if item else "")
                    writer.writerow(rowdata)

            self._show_success("Prédios exportados para CSV com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{str(e)}")

    def exportar_pdf(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar prédios para PDF", "predios.pdf", "PDF (*.pdf)"
        )
        if not filename:
            return

        try:
            styles = getSampleStyleSheet()
            estilo = styles["BodyText"]
            estilo.fontName = "Helvetica"
            estilo.fontSize = 9
            estilo.leading = 11

            colunas_visiveis = [
                col for col in range(self.table.columnCount())
                if not self.table.isColumnHidden(col)
            ]

            headers = [
                Paragraph(self.table.horizontalHeaderItem(col).text(), styles["Heading5"])
                for col in colunas_visiveis
            ]

            data = [headers]

            for row in range(self.table.rowCount()):
                rowdata = []
                for col in colunas_visiveis:
                    item = self.table.item(row, col)
                    texto = item.text() if item else ""
                    rowdata.append(Paragraph(texto.replace("\n", "<br/>"), estilo))
                data.append(rowdata)

            doc = SimpleDocTemplate(filename, pagesize=A4)

            largura_util = A4[0] - doc.leftMargin - doc.rightMargin
            qtd_cols = len(colunas_visiveis)
            col_width = largura_util / qtd_cols if qtd_cols else largura_util
            col_widths = [col_width] * qtd_cols

            tabela = Table(data, colWidths=col_widths, repeatRows=1)
            tabela.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]))

            doc.build([tabela])
            self._show_success("Prédios exportados para PDF com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{str(e)}")