import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QFileDialog, QMessageBox, QLabel, QComboBox
)

from utils.utils_log import (
    LOG_FILE,
    TECHNICAL_LOG_FILE,
    get_daily_audit_log_path,
    get_daily_app_log_path,
    get_legacy_audit_log_path,
    get_logger,
)
from utils.button_style import aplicar_estilo_botao_padrao
import config

logger = get_logger(__name__)


class LogViewerTab(QWidget):
    def __init__(self):
        super().__init__()
        logger.info("Inicializando aba de visualização de logs")

        layout = QVBoxLayout(self)

        top_bar = QHBoxLayout()
        self.lbl_tipo = QLabel("Tipo de log:")
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem("Auditoria", str(get_daily_audit_log_path()))
        self.combo_tipo.addItem("Técnico", str(get_daily_app_log_path()))

        self.btn_refresh = QPushButton("Atualizar Logs")
        self.btn_export = QPushButton("Exportar Logs (TXT)")

        aplicar_estilo_botao_padrao(
            self.btn_refresh,
            config.COLOR_BTN_AZUL,
            config.COLOR_BTN_TEXTO,
        )
        aplicar_estilo_botao_padrao(
            self.btn_export,
            config.COLOR_BTN_LARANJA,
            config.COLOR_BTN_TEXTO_ESCURO,
        )

        top_bar.addWidget(self.lbl_tipo)
        top_bar.addWidget(self.combo_tipo)
        top_bar.addWidget(self.btn_refresh)
        top_bar.addWidget(self.btn_export)

        self.text_logs = QTextEdit()
        self.text_logs.setReadOnly(True)

        layout.addLayout(top_bar)
        layout.addWidget(self.text_logs)
        self.setLayout(layout)

        self.combo_tipo.currentIndexChanged.connect(self.carregar_logs)
        self.btn_refresh.clicked.connect(self.carregar_logs)
        self.btn_export.clicked.connect(self.exportar_logs)

        self.carregar_logs()

    def _get_dash_main(self):
        janela = self.parentWidget()
        while janela is not None and janela.__class__.__name__ != "DashMain":
            janela = janela.parentWidget()
        return janela

    def _arquivo_log_atual(self):
        return self.combo_tipo.currentData()

    def _nome_log_atual(self):
        return self.combo_tipo.currentText()

    def _resolver_arquivo_log(self):
        arquivo = self._arquivo_log_atual()
        tipo = self._nome_log_atual()

        if tipo == "Auditoria":
            if arquivo and os.path.exists(arquivo):
                return arquivo

            legado = str(get_legacy_audit_log_path())
            if os.path.exists(legado):
                logger.info(
                    "Arquivo diário de auditoria não encontrado; usando arquivo legado: %s",
                    legado
                )
                return legado

        return arquivo

    def carregar_logs(self):
        arquivo = self._resolver_arquivo_log()
        tipo = self._nome_log_atual()
        logger.info("Carregando log na interface: tipo=%s arquivo=%s", tipo, arquivo)

        try:
            if not arquivo:
                logger.warning("Nenhum arquivo de log configurado para o tipo selecionado")
                self.text_logs.setPlainText("Nenhum arquivo de log configurado.")
                return

            if not os.path.exists(arquivo):
                logger.warning("Arquivo de log não encontrado: %s", arquivo)
                self.text_logs.setPlainText(f"Nenhum log encontrado para: {tipo}.")
                return

            with open(arquivo, "r", encoding="utf-8") as f:
                conteudo = f.read()

            if not conteudo.strip():
                logger.info("Arquivo de log vazio: %s", arquivo)
                self.text_logs.setPlainText(f"O log '{tipo}' está vazio.")
                return

            self.text_logs.setPlainText(conteudo)
            logger.info("Log carregado com sucesso: tipo=%s", tipo)

        except Exception:
            logger.exception("Erro ao carregar log: tipo=%s arquivo=%s", tipo, arquivo)
            self.text_logs.setPlainText(f"Erro ao carregar logs de '{tipo}'.")

    def exportar_logs(self):
        tipo = self._nome_log_atual()
        nome_padrao = f"log_{tipo.lower()}.txt"

        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Logs",
            nome_padrao,
            "Arquivo de texto (*.txt)"
        )
        if not caminho:
            logger.info("Exportação de log cancelada pelo operador: tipo=%s", tipo)
            return

        try:
            texto = self.text_logs.toPlainText()
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(texto)

            logger.info("Log exportado com sucesso: tipo=%s destino=%s", tipo, caminho)

            dash = self._get_dash_main()
            if dash is not None and hasattr(dash, "show_operation_done"):
                dash.show_operation_done(f"Exportação de log '{tipo}' concluída.")
            else:
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Exportação de log '{tipo}' concluída."
                )

        except Exception:
            logger.exception("Erro ao exportar log: tipo=%s destino=%s", tipo, caminho)
            QMessageBox.critical(self, "Erro", f"Erro ao exportar logs de '{tipo}'.")