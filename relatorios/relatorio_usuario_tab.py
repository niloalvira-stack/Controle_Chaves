from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QComboBox, QLabel, QHeaderView, QApplication
)
from PyQt5.QtCore import QTimer, Qt
from datetime import datetime
import csv
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from autenticacao.helpers_autenticacao import get_db_connection


def formatar_data_br(valor):
    if not valor:
        return ""
    try:
        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y %H:%M:%S")
        return datetime.strptime(valor, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(valor)


class RelatorioPorUsuarioTab(QWidget):
    def __init__(self):
        super().__init__()
        self._rows_cache = []
        layout = QVBoxLayout(self)

        # Filtro
        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Utilizador:"))
        self.cb_usuario = QComboBox()
        filtro_layout.addWidget(self.cb_usuario)

        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_filtrar.setObjectName("btnFiltrarUsuario")
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
        self.btn_exportar.setObjectName("btnExportarUsuarioCsv")
        self.btn_exportar.clicked.connect(self.exportar_csv)
        btns_layout.addWidget(self.btn_exportar)

        self.btn_exportar_pdf = QPushButton("Exportar para PDF")
        self.btn_exportar_pdf.setObjectName("btnExportarUsuarioPdf")
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
        self.load_usuarios()
        self.table.setRowCount(0)

        # Auto-refresh mais leve
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(10000)

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

    def _get_dash_main(self):
        app = QApplication.instance()
        if not app:
            return None
        for widget in app.topLevelWidgets():
            if widget.__class__.__name__ == "DashMain":
                return widget
        return None

    def refresh(self):
        usuario_id_atual = self.cb_usuario.currentData()
        self.load_usuarios()
        if usuario_id_atual is not None:
            for idx in range(self.cb_usuario.count()):
                if self.cb_usuario.itemData(idx) == usuario_id_atual:
                    self.cb_usuario.setCurrentIndex(idx)
                    break
        self.load_relatorio()

    def load_usuarios(self):
        usuario_id_atual = self.cb_usuario.currentData()
        self.cb_usuario.blockSignals(True)
        self.cb_usuario.clear()
        self.cb_usuario.addItem("[Selecione um utilizador]", None)

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT u.id, u.nome
            FROM utilizadores u
            JOIN movimentacoes m ON m.utilizador_id = u.id
            ORDER BY u.nome
        """)
        rows = c.fetchall()
        conn.close()

        for uid, nome in rows:
            self.cb_usuario.addItem(nome, uid)

        if usuario_id_atual is not None:
            for idx in range(self.cb_usuario.count()):
                if self.cb_usuario.itemData(idx) == usuario_id_atual:
                    self.cb_usuario.setCurrentIndex(idx)
                    break

        self.cb_usuario.blockSignals(False)

    def _query_base(self):
        # Mesma lógica de COALESCE de antes, adaptada para %s. [web:22][web:103]
        return """
            SELECT m.chave,
                   COALESCE(u.nome, m.usuario) AS utilizador,
                   m.status,
                   m.data_retirada,
                   m.data_retorno
            FROM movimentacoes m
            LEFT JOIN utilizadores u ON u.id = m.utilizador_id
            WHERE u.id = %s
               OR (u.id IS NULL AND m.usuario = %s)
            ORDER BY m.data_retirada DESC
        """

    def _buscar_dados(self):
        idx = self.cb_usuario.currentIndex()
        usuario_id = self.cb_usuario.itemData(idx)
        usuario_nome = self.cb_usuario.currentText()

        if usuario_id is None or self.cb_usuario.currentText().startswith("[Selecione"):
            self._rows_cache = []
            return []

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(self._query_base(), (usuario_id, usuario_nome))
        rows = cursor.fetchall()
        conn.close()
        self._rows_cache = rows
        return rows

    def load_relatorio(self):
        try:
            rows = self._buscar_dados()
            self.table.setRowCount(0)

            if not rows:
                self.lbl_total.setText("0 registros")
                return

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    if j in (3, 4):  # datas
                        val = formatar_data_br(val)
                    item = QTableWidgetItem(str(val) if val else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(i, j, item)

            self.lbl_total.setText(f"{len(rows)} registros")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar relatório:\n{e}")

    def exportar_csv(self):
        if not self._rows_cache:
            self._buscar_dados()

        if not self._rows_cache:
            QMessageBox.information(self, "Exportar CSV", "Não há dados para exportar.")
            return

        usuario_nome = self.cb_usuario.currentText() or "usuario"
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        nome_sugestao = f"relatorio_usuario_{usuario_nome}_{ts}.csv".replace(" ", "_")

        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar relatório por utilizador",
            nome_sugestao,
            "CSV Files (*.csv)"
        )
        if not caminho:
            return

        try:
            with open(caminho, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["Chave", "Utilizador", "Status", "Retirada", "Devolução"])
                for chave, utilizador, status, retirada, devolucao in self._rows_cache:
                    writer.writerow([
                        chave or "",
                        utilizador or "",
                        status or "",
                        formatar_data_br(retirada),
                        formatar_data_br(devolucao),
                    ])

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_status_message("Relatório por utilizador exportado para CSV.")
            else:
                QMessageBox.information(self, "Exportar CSV", "Exportação concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{e}")

    def exportar_pdf(self):
        if not self._rows_cache:
            self._buscar_dados()

        if not self._rows_cache:
            QMessageBox.information(self, "Exportar PDF", "Não há dados para exportar.")
            return

        usuario_nome = self.cb_usuario.currentText() or "Usuário"
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar relatório por utilizador",
            f"relatorio_usuario_{usuario_nome}_{ts}.pdf".replace(" ", "_"),
            "PDF Files (*.pdf)"
        )
        if not caminho:
            return

        try:
            dados = []
            headers = ["Chave", "Utilizador", "Status", "Retirada", "Devolução"]
            dados.append(headers)

            for chave, utilizador, status, retirada, devolucao in self._rows_cache:
                dados.append([
                    chave or "",
                    utilizador or "",
                    status or "",
                    formatar_data_br(retirada),
                    formatar_data_br(devolucao),
                ])

            doc = SimpleDocTemplate(caminho, pagesize=A4)
            tabela = Table(dados, repeatRows=1)
            tabela.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.gray),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]))

            elementos = [
                Paragraph(f"Relatório por utilizador: {usuario_nome}", None),
                Spacer(1, 8),
                tabela,
            ]
            doc.build(elementos)

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_status_message("Relatório por utilizador exportado para PDF.")
            else:
                QMessageBox.information(self, "Exportar PDF", "Exportação concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{e}")
