import traceback
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QLabel, QApplication, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap

from admin.utilizadores_tab import UtilizadoresTab
from admin.admin import AdminTab
from admin.log_viewer_tab import LogViewerTab
from controle.movimentacoes import MovimentacoesTab, ha_chaves_em_atraso, verificar_pendencias_e_enviar_emails
from relatorios.relatorios_tab import RelatoriosTab
from autenticacao import session_manager
from utils.utils_log import get_logger

import config
from utils.caminhos import caminho_recurso  # ✅ Importa a função que resolve o caminho

logger = get_logger(__name__)


class DashMain(QMainWindow):
    def __init__(self, on_logout=None):
        super().__init__()
        self.on_logout = on_logout
        self._logout_realizado = False

        user = session_manager.current_user
        if not user:
            self.user_login = "?"
            self.user_nome = "Desconhecido"
            self.user_is_admin = False
        else:
            self.user_login = getattr(user, "login", "?")
            self.user_nome = getattr(user, "nome", "Desconhecido")
            self.user_is_admin = getattr(user, "is_admin", False)

        logger.info(
            "Inicializando DashMain para %s (%s)",
            self.user_nome,
            self.user_login
        )

        self.setWindowTitle("Controle de Chaves - Painel Principal")
        self.resize(1024, 768)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout_principal = QVBoxLayout(central_widget)

        # ✅ AVISO DE CHAVES EM ATRASO — CORRIGIDO
        self.lblAlertaChaves = QLabel()
        self.lblAlertaChaves.setStyleSheet(
            "QLabel { background-color: #ffcc00; color: #000; font-weight: bold; padding: 8px; font-size: 12pt; }"
        )
        self.lblAlertaChaves.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblAlertaChaves.hide()
        layout_principal.addWidget(self.lblAlertaChaves)
        layout_principal.addSpacing(12)

        topo_layout = QHBoxLayout()

        self.label_hora = QLabel()
        self.label_hora.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_hora.setStyleSheet(
            "QLabel { background-color: #f8f9fa; color: #212529; "
            "font-size: 24px; font-weight: 500; padding: 10px 14px; "
            "border: 1px solid #dee2e6; border-radius: 4px; }"
        )
        topo_layout.addWidget(self.label_hora)

        topo_spacer = QSpacerItem(
            40, 20,
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )
        topo_layout.addItem(topo_spacer)
        layout_principal.addLayout(topo_layout)

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        caminho_logo = caminho_recurso(config.APP_LOGO_PATH)
        pix = QPixmap(caminho_logo)
        if not pix.isNull():
            pix = pix.scaledToHeight(
                120,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_label.setPixmap(pix)
        else:
            self.logo_label.setText(config.APP_NAME)
            self.logo_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        layout_principal.addWidget(
            self.logo_label,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.tabs = QTabWidget()
        layout_principal.addWidget(self.tabs)

        bottom_bar_layout = QHBoxLayout()

        self.label_usuario_bottom = QLabel(
            f"Utilizador: {self.user_nome} ({self.user_login})"
        )
        self.label_usuario_bottom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_usuario_bottom.setStyleSheet("color: #555; padding: 4px;")
        bottom_bar_layout.addWidget(self.label_usuario_bottom)

        bottom_spacer = QSpacerItem(
            40, 20,
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )
        bottom_bar_layout.addItem(bottom_spacer)

        self.btn_sobre = QPushButton("Sobre")
        self.btn_sobre.clicked.connect(self.mostrar_sobre)
        self.btn_sobre.setStyleSheet(
            f"QPushButton {{ "
            f"background-color: {config.COLOR_BTN_LARANJA}; "
            f"color: {config.COLOR_BTN_TEXTO_ESCURO}; "
            f"padding: 6px 12px; border-radius: 6px; }}"
        )
        bottom_bar_layout.addWidget(self.btn_sobre)

        self.btn_logout = QPushButton("Logout")
        self.btn_logout.clicked.connect(self.confirmar_logout)
        self.btn_logout.setStyleSheet(
            f"QPushButton {{ "
            f"background-color: {config.COLOR_BTN_AZUL}; "
            f"color: {config.COLOR_BTN_TEXTO}; "
            f"padding: 6px 12px; border-radius: 6px; }}"
        )
        bottom_bar_layout.addWidget(self.btn_logout)

        self.btn_sair = QPushButton("Sair")
        self.btn_sair.clicked.connect(self.sair)
        self.btn_sair.setStyleSheet(
            f"QPushButton {{ "
            f"background-color: {config.COLOR_BTN_VERDE}; "
            f"color: {config.COLOR_BTN_TEXTO}; "
            f"padding: 6px 12px; border-radius: 6px; }}"
        )
        bottom_bar_layout.addWidget(self.btn_sair)

        layout_principal.addLayout(bottom_bar_layout)

        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_label.setStyleSheet(
            "QLabel { background-color: #dff0d8; color: #3c763d; padding: 6px; }"
        )
        self.feedback_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        self.feedback_label.hide()
        layout_principal.addWidget(self.feedback_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizar_hora)
        self.timer.start(1000)
        self.atualizar_hora()

        self.load_tabs()

        # ✅ Timer para verificar chaves em atraso a cada 30 segundos
        self.timer_chaves_atraso = QTimer(self)
        self.timer_chaves_atraso.timeout.connect(self.verificar_chaves_atraso)
        self.timer_chaves_atraso.start(30000)
        self.verificar_chaves_atraso()  # ✅ Verifica IMEDIATAMENTE ao abrir

    def atualizar_hora(self):
        self.label_hora.setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    # ✅ FUNÇÃO CORRIGIDA — Aqui estava o ERRO PRINCIPAL!
    def verificar_chaves_atraso(self):
        """Verifica quantidade de chaves em atraso e mostra aviso no topo da tela"""
        try:
            qtd = ha_chaves_em_atraso()  # ✅ Retorna NÚMERO, não tupla!

            if qtd > 0:
                self.lblAlertaChaves.setText(f"⚠️ HÁ {qtd} CHAVE(S) EM ATRASO! Verifique a devolução.")
                self.lblAlertaChaves.show()
                logger.info(f"✅ {qtd} chave(s) em atraso — aviso exibido")
            else:
                self.lblAlertaChaves.hide()
                logger.info("✅ Nenhuma chave em atraso")

        except Exception as e:
            logger.exception("Erro ao verificar chaves em atraso")
            self.lblAlertaChaves.hide()

    def mostrar_sobre(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Sobre")
        msg.setText(
            f"{config.APP_NAME}\n"
            f"Versão: {config.APP_VERSION}\n"
            f"{config.APP_COMPANY}"
        )

        caminho_logo = caminho_recurso(config.APP_LOGO_PATH)
        pix = QPixmap(caminho_logo)
        if not pix.isNull():
            pix = pix.scaled(
                96,
                96,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            msg.setIconPixmap(pix)
        else:
            msg.setIcon(QMessageBox.Icon.Information)

        msg.exec()

    def show_operation_done(self, mensagem="Operação concluída"):
        self.feedback_label.setText(mensagem)
        self.feedback_label.show()
        QTimer.singleShot(4000, self.feedback_label.hide)

    def load_tabs(self):
        self.tabs.clear()
        self.mov_tab = None
        self.rel_tab = None
        self.util_tab = None
        self.admin_tab = None
        self.logs_tab = None

        try:
            self.mov_tab = MovimentacoesTab()
            self.tabs.addTab(self.mov_tab, "Movimentações")
        except Exception:
            logger.exception("Erro na aba Movimentações")
            QMessageBox.critical(
                self,
                "Erro",
                "Falha ao carregar aba Movimentações."
            )

        try:
            self.rel_tab = RelatoriosTab()
            self.tabs.addTab(self.rel_tab, "Relatórios")
        except Exception as e:
            erro = traceback.format_exc()
            logger.exception("Erro na aba Relatórios")

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Erro")
            msg.setText("Falha ao carregar aba Relatórios.")
            msg.setInformativeText(str(e))
            msg.setDetailedText(erro)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()

        try:
            if self.mov_tab is not None:
                self.util_tab = UtilizadoresTab(self.mov_tab)
            else:
                self.util_tab = UtilizadoresTab(None)

            self.tabs.addTab(self.util_tab, "Utilizadores")
        except Exception:
            logger.exception("Erro na aba Utilizadores")
            QMessageBox.critical(
                self,
                "Erro",
                "Falha ao carregar aba Utilizadores."
            )

        if self.user_is_admin:
            try:
                self.admin_tab = AdminTab({
                    "login": self.user_login,
                    "nome": self.user_nome,
                    "is_admin": True
                })
                self.tabs.addTab(self.admin_tab, "Administração")

                self.logs_tab = LogViewerTab()
                self.tabs.addTab(self.logs_tab, "Logs")

            except Exception as e:
                logger.exception("Erro nas abas de admin")
                QMessageBox.warning(
                    self,
                    "Erro",
                    f"Falha ao carregar permissões:\n{e}"
                )

    def _executar_logout(self):
        if self._logout_realizado:
            return

        try:
            session_manager.logout()
            self._logout_realizado = True
            logger.info(
                "Logout realizado para %s (%s)",
                self.user_nome,
                self.user_login
            )
        except Exception:
            erro_completo = traceback.format_exc()
            logger.exception("Erro ao realizar logout")
            QMessageBox.warning(
                self,
                "Erro",
                f"Falha ao realizar logout:\n\n{erro_completo}"
            )

    def confirmar_logout(self):
        resp = QMessageBox.question(
            self,
            "Logout",
            "Deseja sair?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if resp == QMessageBox.StandardButton.Yes:
            if self.on_logout:
                self.on_logout()
            else:
                self.close()

    def sair(self):
        QApplication.instance().quit()

    def closeEvent(self, event):
        try:
            if hasattr(self, "timer") and self.timer.isActive():
                self.timer.stop()

            if hasattr(self, "timer_chaves_atraso") and self.timer_chaves_atraso.isActive():
                self.timer_chaves_atraso.stop()
        except Exception:
            logger.exception("Erro durante o fechamento da janela")
        finally:
            super().closeEvent(event)