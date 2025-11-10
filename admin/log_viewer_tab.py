import self
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton
from utils.utils_log import LOG_FILE

LOG_FILE = "controle_chaves.log"

# admin/log_viewer_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton
from utils.utils_log import LOG_FILE

class LogViewerTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.text_logs = QTextEdit()
        self.text_logs.setReadOnly(True)

        btn_refresh = QPushButton("Atualizar Logs")
        btn_refresh.clicked.connect(self.carregar_logs)

        layout.addWidget(self.text_logs)
        layout.addWidget(btn_refresh)

        self.setLayout(layout)
        self.carregar_logs()

    def carregar_logs(self):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                conteudo = f.read()
                self.text_logs.setPlainText(conteudo)
        except Exception as e:
            self.text_logs.setPlainText(f"Erro ao carregar logs: {e}")
