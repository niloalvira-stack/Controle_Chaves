from PyQt6.QtWidgets import QWidget, QMessageBox, QApplication, QTableWidgetItem
from PyQt6.QtCore import Qt
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .workers import QueryThread


class BaseRelatorioTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ja_carregou = False
        self._rows_cache = []
        self._loader = None
        self._carregando = False

    def carregar_inicial(self):
        if self._ja_carregou:
            return
        self._ja_carregou = True
        self.load_relatorio()

    def _get_dash_main(self):
        app = QApplication.instance()
        if not app:
            return None
        for widget in app.topLevelWidgets():
            if widget.__class__.__name__ == "DashMain":
                return widget
        return None

    def _iniciar_query(self, sql, params=(), on_loaded=None):
        if self._carregando:
            return

        self._carregando = True
        self._loader = QueryThread(sql, params, self)
        self._loader.loaded.connect(on_loaded or self._on_loaded_default)
        self._loader.error.connect(self._on_error)
        self._loader.finished.connect(self._on_finished)
        self._loader.finished.connect(self._loader.deleteLater)
        self._loader.start()

    def _on_loaded_default(self, rows):
        self._rows_cache = rows or []

    def _on_error(self, msg):
        QMessageBox.critical(self, "Erro", msg)

    def _on_finished(self):
        self._carregando = False
        self._loader = None

    def _preencher_tablewidget(self, table, rows, date_indexes=None, formatter=None):
        date_indexes = date_indexes or set()

        table.setUpdatesEnabled(False)
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(rows))

        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j in date_indexes and formatter:
                    val = formatter(val)
                item = QTableWidgetItem(str(val) if val is not None else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(i, j, item)

        table.setUpdatesEnabled(True)
        table.viewport().update()

    def _garantir_extensao(self, path, extensao):
        if not path:
            return path
        ext = extensao.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        if not path.lower().endswith(ext):
            path += ext
        return path

    def _notificar_exportacao_ok(self, msg_dash, titulo_box="Sucesso", msg_box="Exportação concluída."):
        dash = self._get_dash_main()
        if dash is not None:
            dash.show_status_message(msg_dash)
        else:
            QMessageBox.information(self, titulo_box, msg_box)

    def _criar_estilos_pdf_padrao(self):
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

        style_title = styles["Title"].clone("report_title")
        style_title.alignment = TA_CENTER
        style_title.fontName = "Helvetica-Bold"
        style_title.fontSize = 14
        style_title.leading = 18

        return style_title, style_header, style_cell

    def _criar_tabela_pdf_padrao(self, dados, col_widths, repeat_rows=1):
        tabela = Table(dados, colWidths=col_widths, repeatRows=repeat_rows)
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
        return tabela