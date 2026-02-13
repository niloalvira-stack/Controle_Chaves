# admin/log_viewer_tab.py

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QFileDialog, QMessageBox
)
from utils.utils_log import LOG_FILE  # caminho já definido no utils_log


class LogViewerTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.text_logs = QTextEdit()
        self.text_logs.setReadOnly(True)

        self.btn_refresh = QPushButton("Atualizar Logs")
        self.btn_export = QPushButton("Exportar Logs (TXT)")

        self.btn_refresh.clicked.connect(self.carregar_logs)
        self.btn_export.clicked.connect(self.exportar_logs)

        layout.addWidget(self.text_logs)
        layout.addWidget(self.btn_refresh)
        layout.addWidget(self.btn_export)

        self.setLayout(layout)
        self.carregar_logs()

    def _get_dash_main(self):
        janela = self.parentWidget()
        while janela is not None and janela.__class__.__name__ != "DashMain":
            janela = janela.parentWidget()
        return janela

    def carregar_logs(self):
        try:
            if not os.path.exists(LOG_FILE):
                self.text_logs.setPlainText("Nenhum log encontrado.")
                return
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                conteudo = f.read()
                self.text_logs.setPlainText(conteudo)
        except Exception as e:
            self.text_logs.setPlainText(f"Erro ao carregar logs: {e}")

    def exportar_logs(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Logs",
            "",
            "Arquivo de texto (*.txt)"
        )
        if not caminho:
            return
        try:
            texto = self.text_logs.toPlainText()
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(texto)

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Exportação de logs concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar logs: {e}")
