import csv
from datetime import datetime, time

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QFileDialog,
    QMessageBox, QDateEdit, QLabel, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import QDate
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from relatorios.base_relatorio_tab import BaseRelatorioTab
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


class RelatorioPorPeriodoTab(BaseRelatorioTab):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        filtros_layout = QHBoxLayout()
        filtros_layout.addWidget(QLabel("Data Início:"))

        self.data_inicio = QDateEdit()
        self.data_inicio.setCalendarPopup(True)
        self.data_inicio.setDisplayFormat("dd/MM/yyyy")
        self.data_inicio.setDate(QDate.currentDate())
        filtros_layout.addWidget(self.data_inicio)

        filtros_layout.addWidget(QLabel("Data Fim:"))
        self.data_fim = QDateEdit()
        self.data_fim.setCalendarPopup(True)
        self.data_fim.setDisplayFormat("dd/MM/yyyy")
        self.data_fim.setDate(QDate.currentDate())
        filtros_layout.addWidget(self.data_fim)

        self.btn_filtrar = criar_botao_padrao(
            "Filtrar",
            role="primary",
            slot=self.load_relatorio
        )
        filtros_layout.addWidget(self.btn_filtrar)

        self.lbl_total = QLabel("0 registros")
        filtros_layout.addWidget(self.lbl_total)

        filtros_layout.addStretch()
        layout.addLayout(filtros_layout)

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

    def _periodo(self):
        di = self.data_inicio.date().toPyDate()
        df = self.data_fim.date().toPyDate()

        if di > df:
            raise ValueError("A data inicial não pode ser maior que a data final.")

        inicio = datetime.combine(di, time.min)
        fim = datetime.combine(df, time.max)
        return inicio, fim

    def _query_base(self):
        return """
            SELECT m.chave,
                   COALESCE(u.nome, m.usuario) AS utilizador,
                   m.status,
                   m.data_retirada,
                   m.data_retorno
            FROM movimentacoes m
            LEFT JOIN utilizadores u ON u.id = m.utilizador_id
            WHERE m.data_retirada BETWEEN %s AND %s
            ORDER BY m.data_retirada DESC
        """

    def load_relatorio(self):
        if self._carregando:
            return

        try:
            inicio, fim = self._periodo()
        except ValueError as e:
            QMessageBox.warning(self, "Período inválido", str(e))
            return

        self.btn_filtrar.setEnabled(False)
        self._iniciar_query(
            self._query_base(),
            (inicio, fim),
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
            QMessageBox.information(self, "Informação", "Nenhum registro para exportar.")
            return

        inicio = self.data_inicio.date().toString("yyyyMMdd")
        fim = self.data_fim.date().toString("yyyyMMdd")
        nome_sugestao = f"relatorio_periodo_{inicio}_a_{fim}.csv"

        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar CSV", nome_sugestao, "CSV Files (*.csv)"
        )
        if not path:
            return

        if not path.lower().endswith(".csv"):
            path += ".csv"

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
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
                show_status("Exportação CSV por período concluída.")
            else:
                QMessageBox.information(self, "Sucesso", "Exportação CSV concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{e}")

    def exportar_pdf(self):
        if not self._rows_cache:
            QMessageBox.information(self, "Informação", "Nenhum registro para exportar.")
            return

        inicio = self.data_inicio.date().toString("yyyyMMdd")
        fim = self.data_fim.date().toString("yyyyMMdd")
        nome_sugestao = f"relatorio_periodo_{inicio}_a_{fim}.pdf"

        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar PDF", nome_sugestao, "PDF Files (*.pdf)"
        )
        if not path:
            return

        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        try:
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
                bottomMargin=bottom_margin,
            )

            periodo_str = (
                f"{self.data_inicio.date().toString('dd/MM/yyyy')} a "
                f"{self.data_fim.date().toString('dd/MM/yyyy')}"
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

            story = [
                Paragraph(
                    f"Relatório de Movimentações por Período<br/>{periodo_str}",
                    style_titulo
                ),
                Spacer(1, 12),
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

            story.append(tabela)
            pdf.build(story)

            dash = self._get_dash_main()
            show_status = getattr(dash, "show_status_message", None)

            if callable(show_status):
                show_status("Exportação PDF por período concluída.")
            else:
                QMessageBox.information(self, "Sucesso", "Exportação PDF concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{e}")