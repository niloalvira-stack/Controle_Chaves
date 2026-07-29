import csv
from datetime import datetime

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QFileDialog,
    QMessageBox, QComboBox, QLabel, QHeaderView, QAbstractItemView
)
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from .base_relatorio_tab import BaseRelatorioTab
from .workers import QueryThread
from utils.ui_buttons import criar_botao_padrao


def formatar_data_br(valor):
    if not valor:
        return ""
    try:
        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y %H:%M:%S")
        return datetime.strptime(
            str(valor),
            "%Y-%m-%d %H:%M:%S"
        ).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(valor)


class RelatorioPorUsuarioTab(BaseRelatorioTab):
    def __init__(self):
        super().__init__()
        self._usuarios_loader = None

        layout = QVBoxLayout(self)
        filtro_layout = QHBoxLayout()
        # ✅ Renomeado para "Utilizador:" como você pediu
        filtro_layout.addWidget(QLabel("Utilizador:"))

        self.cb_usuario = QComboBox()
        # ✅ Ajustes de largura para ver o nome completo
        self.cb_usuario.setMinimumWidth(380)
        self.cb_usuario.view().setMinimumWidth(400)
        self.cb_usuario.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        filtro_layout.addWidget(self.cb_usuario)

        # ✅ CRIA O BOTÃO QUE ESTAVA FALTANDO
        self.btn_filtrar = criar_botao_padrao(
            "Filtrar",
            role="primary",
            slot=self.load_relatorio
        )
        filtro_layout.addWidget(self.btn_filtrar)

        self.lbl_total = QLabel("0 registros")
        filtro_layout.addWidget(self.lbl_total)

        filtro_layout.addStretch()
        layout.addLayout(filtro_layout)

        filtro_layout.addWidget(self.btn_filtrar)

        self.lbl_total = QLabel("0 registros")
        filtro_layout.addWidget(self.lbl_total)

        filtro_layout.addStretch()
        layout.addLayout(filtro_layout)

        btns_layout = QHBoxLayout()

        self.btn_exportar = criar_botao_padrao(
            "Exportar para CSV",
            role="secondary",
            slot=self.exportar_csv
        )
        btns_layout.addWidget(self.btn_exportar)

        self.btn_exportar_pdf = criar_botao_padrao(
            "Exportar para PDF",
            role="success",
            slot=self.exportar_pdf
        )
        btns_layout.addWidget(self.btn_exportar_pdf)

        btns_layout.addStretch()
        layout.addLayout(btns_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Chave", "Utilizador", "Status", "Retirada", "Devolução"]
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

    def carregar_inicial(self):
        if self._ja_carregou:
            return
        self._ja_carregou = True
        self.load_usuarios()

    def load_usuarios(self):
        if self._usuarios_loader is not None:
            return

        sql = """
            SELECT DISTINCT u.id, u.nome
            FROM utilizadores u
            JOIN movimentacoes m ON m.utilizador_id = u.id
            ORDER BY u.nome
        """

        self._usuarios_loader = QueryThread(sql, parent=self)
        self._usuarios_loader.loaded.connect(self._on_usuarios_loaded)
        self._usuarios_loader.error.connect(self._on_error)
        self._usuarios_loader.finished.connect(self._on_usuarios_finished)
        self._usuarios_loader.finished.connect(self._usuarios_loader.deleteLater)
        self._usuarios_loader.start()

    def _on_usuarios_loaded(self, rows):
        usuario_id_atual = self.cb_usuario.currentData()

        self.cb_usuario.blockSignals(True)
        self.cb_usuario.clear()
        self.cb_usuario.addItem("[Selecione um utilizador]", None)

        for uid, nome in rows or []:
            if isinstance(nome, (bytes, bytearray)):
                nome = nome.decode("utf-8", errors="ignore")
            self.cb_usuario.addItem(nome or "", uid)

        if usuario_id_atual is not None:
            for idx in range(self.cb_usuario.count()):
                if self.cb_usuario.itemData(idx) == usuario_id_atual:
                    self.cb_usuario.setCurrentIndex(idx)
                    break

        self.cb_usuario.blockSignals(False)

    def _on_usuarios_finished(self):
        self._usuarios_loader = None

    def _query_base(self):
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

    def load_relatorio(self):
        if self._carregando:
            return

        idx = self.cb_usuario.currentIndex()
        usuario_id = self.cb_usuario.itemData(idx)
        usuario_nome = self.cb_usuario.currentText()

        if usuario_id is None or usuario_nome.startswith("[Selecione"):
            self._rows_cache = []
            self.table.clearContents()
            self.table.setRowCount(0)
            self.lbl_total.setText("0 registros")
            return

        self.btn_filtrar.setEnabled(False)
        self._iniciar_query(
            self._query_base(),
            (usuario_id, usuario_nome),
            on_loaded=self._on_loaded
        )

    def _on_loaded(self, rows):
        self._rows_cache = rows or []
        self._preencher_tablewidget(
            self.table,
            self._rows_cache,
            date_indexes={3, 4},
            formatter=formatar_data_br
        )
        self.lbl_total.setText(f"{len(self._rows_cache)} registros")

    def _on_finished(self):
        super()._on_finished()
        self.btn_filtrar.setEnabled(True)

    def exportar_csv(self):
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

        if not caminho.lower().endswith(".csv"):
            caminho += ".csv"

        try:
            with open(caminho, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
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
            show_status = getattr(dash, "show_status_message", None)

            if callable(show_status):
                show_status("Relatório por utilizador exportado para CSV.")
            else:
                QMessageBox.information(self, "Exportar CSV", "Exportação concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{e}")

    def exportar_pdf(self):
        if not self._rows_cache:
            QMessageBox.information(self, "Exportar PDF", "Não há dados para exportar.")
            return

        usuario_nome = self.cb_usuario.currentText() or "Usuário"
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        nome_sugestao = f"relatorio_usuario_{usuario_nome}_{ts}.pdf".replace(" ", "_")

        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar relatório por utilizador",
            nome_sugestao,
            "PDF Files (*.pdf)"
        )
        if not caminho:
            return

        if not caminho.lower().endswith(".pdf"):
            caminho += ".pdf"

        try:
            styles = getSampleStyleSheet()
            dados = [[
                Paragraph("Chave", styles["BodyText"]),
                Paragraph("Utilizador", styles["BodyText"]),
                Paragraph("Status", styles["BodyText"]),
                Paragraph("Retirada", styles["BodyText"]),
                Paragraph("Devolução", styles["BodyText"]),
            ]]

            for chave, utilizador, status, retirada, devolucao in self._rows_cache:
                dados.append([
                    Paragraph(str(chave or ""), styles["BodyText"]),
                    Paragraph(str(utilizador or ""), styles["BodyText"]),
                    Paragraph(str(status or ""), styles["BodyText"]),
                    Paragraph(formatar_data_br(retirada), styles["BodyText"]),
                    Paragraph(formatar_data_br(devolucao), styles["BodyText"]),
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
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))

            doc.build([Paragraph(f"Relatório por utilizador: {usuario_nome}", styles["Title"]), Spacer(1, 8), tabela])

            dash = self._get_dash_main()
            show_status = getattr(dash, "show_status_message", None)

            if callable(show_status):
                show_status("Relatório por utilizador exportado para PDF.")
            else:
                QMessageBox.information(self, "Exportar PDF", "Exportação concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{e}")