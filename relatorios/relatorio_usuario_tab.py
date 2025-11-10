from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QComboBox, QLabel, QHeaderView
)
from PyQt5.QtCore import QTimer
from datetime import datetime
import sqlite3
import csv
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

DB_NAME = "controle_chaves.db"


def formatar_data_br(valor):
    if not valor:
        return ""
    try:
        return datetime.strptime(valor, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(valor)


class RelatorioPorUsuarioTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Usuário:"))
        self.cb_usuario = QComboBox()
        filtro_layout.addWidget(self.cb_usuario)

        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_filtrar.setObjectName("btnFiltrarUsuario")
        self.btn_filtrar.clicked.connect(self.load_relatorio)
        filtro_layout.addWidget(self.btn_filtrar)
        layout.addLayout(filtro_layout)

        btns_layout = QHBoxLayout()
        self.btn_exportar = QPushButton("Exportar para CSV")
        self.btn_exportar.setObjectName("btnExportarUsuarioCsv")
        self.btn_exportar.clicked.connect(self.exportar_csv)
        btns_layout.addWidget(self.btn_exportar)

        self.btn_exportar_pdf = QPushButton("Exportar para PDF")
        self.btn_exportar_pdf.setObjectName("btnExportarUsuarioPdf")
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)
        btns_layout.addWidget(self.btn_exportar_pdf)
        layout.addLayout(btns_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Chave", "Usuário", "Status", "Retirada", "Devolução"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.load_usuarios()
        self.table.setRowCount(0)  # começa vazio

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000)

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

            QPushButton#btnFiltrarUsuario {
                background-color: #f9a825;
                color: #333333;
                border: 1px solid #f57f17;
            }
            QPushButton#btnFiltrarUsuario:hover {
                background-color: #fbc02d;
            }
            QPushButton#btnFiltrarUsuario:pressed {
                background-color: #f57f17;
            }

            QPushButton#btnExportarUsuarioCsv {
                background-color: #2e7d32;
                color: white;
                border: 1px solid #1b5e20;
            }
            QPushButton#btnExportarUsuarioCsv:hover {
                background-color: #388e3c;
            }
            QPushButton#btnExportarUsuarioCsv:pressed {
                background-color: #1b5e20;
            }

            QPushButton#btnExportarUsuarioPdf {
                background-color: #1565c0;
                color: white;
                border: 1px solid #0d47a1;
            }
            QPushButton#btnExportarUsuarioPdf:hover {
                background-color: #1976d2;
            }
            QPushButton#btnExportarUsuarioPdf:pressed {
                background-color: #0d47a1;
            }
        """)

    def refresh(self):
        usuario_atual = self.cb_usuario.currentText()
        self.load_usuarios()
        if usuario_atual:
            idx = self.cb_usuario.findText(usuario_atual)
            if idx >= 0:
                self.cb_usuario.setCurrentIndex(idx)
        self.load_relatorio()

    def load_usuarios(self):
        usuario_atual = self.cb_usuario.currentText()
        self.cb_usuario.blockSignals(True)
        self.cb_usuario.clear()
        self.cb_usuario.addItem("[Selecione um usuário]")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT DISTINCT usuario FROM movimentacoes ORDER BY usuario")
        usuarios = [row[0] for row in c.fetchall()]
        self.cb_usuario.addItems(usuarios)
        if usuario_atual:
            idx = self.cb_usuario.findText(usuario_atual)
            if idx >= 0:
                self.cb_usuario.setCurrentIndex(idx)
        self.cb_usuario.blockSignals(False)
        conn.close()

    def load_relatorio(self):
        usuario = self.cb_usuario.currentText()
        if usuario == "[Selecione um usuário]" or not usuario:
            self.table.setRowCount(0)
            return
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chave, usuario, status, data_retirada, data_retorno
                FROM movimentacoes
                WHERE usuario = ?
                ORDER BY data_retirada DESC
            """, (usuario,))
            rows = cursor.fetchall()
            conn.close()

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    if j in (3, 4):  # datas
                        val = formatar_data_br(val)
                    self.table.setItem(i, j, QTableWidgetItem(str(val) if val else ""))
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar relatório:\n{e}")

    def exportar_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        usuario = self.cb_usuario.currentText()
        if usuario == "[Selecione um usuário]" or not usuario:
            QMessageBox.warning(self, "Atenção", "Selecione um usuário para exportar.")
            return
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chave, usuario, status, data_retirada, data_retorno
                FROM movimentacoes
                WHERE usuario = ?
                ORDER BY data_retirada DESC
            """, (usuario,))
            rows = cursor.fetchall()
            conn.close()

            linhas = []
            for chave, usuario, status, data_ret, data_retorn in rows:
                linhas.append([
                    chave,
                    usuario,
                    status,
                    formatar_data_br(data_ret),
                    formatar_data_br(data_retorn),
                ])

            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Chave", "Usuário", "Status", "Retirada", "Devolução"])
                writer.writerows(linhas)
            QMessageBox.information(self, "Sucesso", "Relatório exportado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{e}")

    def exportar_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        usuario = self.cb_usuario.currentText()
        if usuario == "[Selecione um usuário]" or not usuario:
            QMessageBox.warning(self, "Atenção", "Selecione um usuário para exportar.")
            return
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chave, usuario, status, data_retirada, data_retorno
                FROM movimentacoes
                WHERE usuario = ?
                ORDER BY data_retirada DESC
            """, (usuario,))
            rows = cursor.fetchall()
            conn.close()

            cabecalho = ["Chave", "Usuário", "Status", "Retirada", "Devolução"]
            dados = [cabecalho]
            for chave, usuario, status, data_ret, data_retorn in rows:
                dados.append([
                    str(chave) if chave else "",
                    str(usuario) if usuario else "",
                    str(status) if status else "",
                    formatar_data_br(data_ret),
                    formatar_data_br(data_retorn),
                ])

            pdf = SimpleDocTemplate(
                path, pagesize=A4, leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24
            )
            table = Table(dados, repeatRows=1)
            style = TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
                ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE", (0,0), (-1,-1), 9),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("TOPPADDING", (0,0), (-1,-1), 2),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ])
            table.setStyle(style)
            pdf.build([table])
            QMessageBox.information(self, "Exportação", "Relatório PDF exportado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{e}")
