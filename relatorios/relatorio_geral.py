import csv
from datetime import datetime

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QFileDialog,
    QMessageBox, QHeaderView, QAbstractItemView
)
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from .base_relatorio_tab import BaseRelatorioTab
from utils.ui_buttons import criar_botao_padrao


def formatar_data_br(valor):
    if not valor:
        return ""
    try:
        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y %H:%M:%S")
        return datetime.strptime(
            str(valor), "%Y-%m-%d %H:%M:%S"
        ).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(valor)


class RelatorioGeralTab(BaseRelatorioTab):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        btns_layout = QHBoxLayout()

        self.btn_atualizar = criar_botao_padrao(
            "Atualizar",
            role="primary",
            slot=self.load_relatorio
        )
        btns_layout.addWidget(self.btn_atualizar)

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
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Chave", "Utilizador", "Status", "Retirada", "Devolução"]
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setColumnHidden(0, True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        layout.addWidget(self.table)

    def _query_base(self):
        return """
            SELECT m.id,
                   m.chave,
                   COALESCE(u.nome, m.usuario) AS utilizador,
                   m.status,
                   m.data_retirada,
                   m.data_retorno
            FROM movimentacoes m
            LEFT JOIN utilizadores u ON u.id = m.utilizador_id
            ORDER BY m.data_retirada DESC
        """

    def load_relatorio(self):
        if self._carregando:
            return
        self.btn_atualizar.setEnabled(False)
        self._iniciar_query(self._query_base(), on_loaded=self._on_loaded)

    def _on_loaded(self, rows):
        self._rows_cache = rows or []
        self._preencher_tablewidget(
            self.table,
            self._rows_cache,
            date_indexes={4, 5},
            formatter=formatar_data_br
        )

    def _on_finished(self):
        super()._on_finished()
        self.btn_atualizar.setEnabled(True)

    def exportar_csv(self):
        if not self._rows_cache:
            QMessageBox.information(self, "Exportar CSV", "Não há dados para exportar.")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M")
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar CSV", f"relatorio_geral_{ts}.csv", "CSV Files (*.csv)"
        )
        if not path:
            return

        if not path.lower().endswith(".csv"):
            path += ".csv"

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Chave", "Utilizador", "Status", "Retirada", "Devolução"])

                for _id, chave, utilizador, status, retirada, devolucao in self._rows_cache:
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
                show_status("Exportação CSV geral concluída.")
            else:
                QMessageBox.information(self, "Exportar CSV", "Exportação concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{e}")


    def exportar_pdf(self):
        if not self._rows_cache:
            QMessageBox.information(self, "Exportar PDF", "Não há dados para exportar.")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M")
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar PDF", f"relatorio_geral_{ts}.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return

        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        try:
            from reportlab.platypus import Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.enums import TA_CENTER, TA_LEFT

            left_margin = 24
            right_margin = 24
            top_margin = 24
            bottom_margin = 24

            pdf = SimpleDocTemplate(
                path,
                pagesize=A4,
                leftMargin=left_margin,
                rightMargin=right_margin,
                topMargin=top_margin,
                bottomMargin=bottom_margin
            )

            styles = getSampleStyleSheet()
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

            dados = [[
                Paragraph("Chave", style_header),
                Paragraph("Utilizador", style_header),
                Paragraph("Status", style_header),
                Paragraph("Retirada", style_header),
                Paragraph("Devolução", style_header),
            ]]

            for _id, chave, utilizador, status, retirada, devolucao in self._rows_cache:
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

            pdf.build([tabela])

            dash = self._get_dash_main()
            show_status = getattr(dash, "show_status_message", None)

            if callable(show_status):
                show_status("Exportação PDF geral concluída.")
            else:
                QMessageBox.information(self, "Exportar PDF", "Exportação concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{e}")