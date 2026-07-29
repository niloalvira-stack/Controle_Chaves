# relatorios/relatorio_sala_tab.py
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
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .base_relatorio_tab import BaseRelatorioTab
from .workers import QueryThread
from utils.ui_buttons import criar_botao_padrao


def formatar_data_br(valor):
    if not valor:
        return ""
    try:
        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y %H:%M:%S")

        texto = str(valor).strip()
        try:
            return datetime.fromisoformat(texto).strftime("%d/%m/%Y %H:%M:%S")
        except ValueError:
            return datetime.strptime(
                texto, "%Y-%m-%d %H:%M:%S"
            ).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(valor)


class RelatorioPorSalaTab(BaseRelatorioTab):
    def __init__(self):
        super().__init__()
        self._salas_loader = None

        layout = QVBoxLayout(self)

        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Sala:"))

        self.cb_sala = QComboBox()
        # ✅ Ajustes de largura
        self.cb_sala.setMinimumWidth(380)
        self.cb_sala.view().setMinimumWidth(400)
        self.cb_sala.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

        filtro_layout.addWidget(self.cb_sala)

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
        self.load_salas()

    def load_salas(self):
        if self._salas_loader is not None:
            return

        sql = """
            SELECT s.id,
                   COALESCE(NULLIF(TRIM(s.nome), ''), 'Sem nome') AS nome
            FROM salas s
            WHERE COALESCE(s.status, 'ativo') <> 'inativo'
            ORDER BY nome
        """

        self._salas_loader = QueryThread(sql, parent=self)
        self._salas_loader.loaded.connect(self._on_salas_loaded)
        self._salas_loader.error.connect(self._on_error)
        self._salas_loader.finished.connect(self._on_salas_finished)
        self._salas_loader.finished.connect(self._salas_loader.deleteLater)
        self._salas_loader.start()

    def _on_salas_loaded(self, rows):
        sala_id_atual = self.cb_sala.currentData()

        self.cb_sala.blockSignals(True)
        self.cb_sala.clear()
        self.cb_sala.addItem("[Selecione uma sala]", None)

        for sid, nome in rows or []:
            if isinstance(nome, (bytes, bytearray)):
                nome = nome.decode("utf-8", errors="ignore")
            self.cb_sala.addItem(nome or "Sem nome", sid)

        if sala_id_atual is not None:
            for idx in range(self.cb_sala.count()):
                if self.cb_sala.itemData(idx) == sala_id_atual:
                    self.cb_sala.setCurrentIndex(idx)
                    break

        self.cb_sala.blockSignals(False)

    def _on_salas_finished(self):
        self._salas_loader = None

    def _query_base(self):
        return """
            SELECT m.chave,
                   COALESCE(u.nome, m.usuario) AS utilizador,
                   m.status,
                   m.data_retirada,
                   m.data_retorno
            FROM movimentacoes m
            LEFT JOIN utilizadores u ON u.id = m.utilizador_id
            INNER JOIN salas s ON s.id = m.sala_id
            WHERE s.id = %s
            ORDER BY m.data_retirada DESC
        """

    def load_relatorio(self):
        if self._carregando:
            return

        sala_id = self.cb_sala.currentData()

        if sala_id is None or self.cb_sala.currentText().startswith("[Selecione"):
            self._rows_cache = []
            self.table.clearContents()
            self.table.setRowCount(0)
            self.lbl_total.setText("0 registros")
            return

        self.btn_filtrar.setEnabled(False)
        self._iniciar_query(self._query_base(), (sala_id,), on_loaded=self._on_loaded)

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

        sala = self.cb_sala.currentText() or "sala"
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        nome_sugestao = f"relatorio_sala_{sala}_{ts}.csv".replace(" ", "_")

        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar relatório por sala",
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
                show_status("Relatório por sala exportado para CSV.")
            else:
                QMessageBox.information(self, "Exportar CSV", "Exportação concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{e}")

    def exportar_pdf(self):
        if not self._rows_cache:
            QMessageBox.information(self, "Exportar PDF", "Não há dados para exportar.")
            return

        sala = self.cb_sala.currentText() or "Sala"
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar relatório por sala",
            f"relatorio_sala_{sala}_{ts}.pdf".replace(" ", "_"),
            "PDF Files (*.pdf)"
        )
        if not caminho:
            return

        if not caminho.lower().endswith(".pdf"):
            caminho += ".pdf"

        try:
            left_margin = 24
            right_margin = 24
            top_margin = 24
            bottom_margin = 24

            doc = SimpleDocTemplate(
                caminho,
                pagesize=A4,
                leftMargin=left_margin,
                rightMargin=right_margin,
                topMargin=top_margin,
                bottomMargin=bottom_margin
            )

            styles = getSampleStyleSheet()

            style_titulo = styles["Title"].clone("titulo_relatorio")
            style_titulo.fontName = "Helvetica-Bold"
            style_titulo.fontSize = 14
            style_titulo.leading = 18
            style_titulo.alignment = TA_CENTER

            style_header = styles["Heading5"].clone("table_header")
            style_header.alignment = TA_CENTER
            style_header.fontName = "Helvetica-Bold"
            style_header.fontSize = 9
            style_header.leading = 11

            style_cell = styles["BodyText"].clone("table_cell")
            style_cell.alignment = TA_LEFT
            style_cell.fontName = "Helvetica"
            style_cell.fontSize = 8
            style_cell.leading = 10

            elementos = [
                Paragraph(f"Relatório por sala: {sala}", style_titulo),
                Spacer(1, 10),
            ]

            dados = [[
                Paragraph("Chave", style_header),
                Paragraph("Utilizador", style_header),
                Paragraph("Status", style_header),
                Paragraph("Retirada", style_header),
                Paragraph("Devolução", style_header),
            ]]

            for chave, utilizador, status, retirada, devolucao in self._rows_cache:
                dados.append([
                    Paragraph(str(chave or ""), style_cell),
                    Paragraph(str(utilizador or ""), style_cell),
                    Paragraph(str(status or ""), style_cell),
                    Paragraph(formatar_data_br(retirada), style_cell),
                    Paragraph(formatar_data_br(devolucao), style_cell),
                ])

            largura_util = A4[0] - left_margin - right_margin
            col_widths = [
                largura_util * 0.18,
                largura_util * 0.28,
                largura_util * 0.14,
                largura_util * 0.20,
                largura_util * 0.20,
            ]

            tabela = Table(dados, colWidths=col_widths, repeatRows=1)
            tabela.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))

            elementos.append(tabela)
            doc.build(elementos)

            dash = self._get_dash_main()
            show_status = getattr(dash, "show_status_message", None)

            if callable(show_status):
                show_status("Relatório por sala exportado para PDF.")
            else:
                QMessageBox.information(self, "Exportar PDF", "Exportação concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{e}")