import config
from utils.caminhos import caminho_recurso
import traceback
from datetime import datetime

from admin.utilizadores_tab import UtilizadoresTab
from admin.admin import AdminTab
from admin.log_viewer_tab import LogViewerTab
from controle.movimentacoes import MovimentacoesTab, ha_chaves_em_atraso
from relatorios.relatorios_tab import RelatoriosTab

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QLabel, QApplication, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap

from autenticacao import session_manager
from utils.utils_log import get_logger

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
            self.eh_admin = False
        else:
            self.user_login = getattr(user, "login", "?")
            self.user_nome = getattr(user, "nome", "Desconhecido")
            self.eh_admin = getattr(user, "is_admin", False)

        logger.info(
            "Inicializando DashMain para %s (%s)",
            self.user_nome, self.user_login
        )
        print(f"🔍 DASH — usuario={self.user_login} | eh_admin={self.eh_admin}")

        self.setWindowTitle("Controle de Chaves - Painel Principal")
        self.resize(1024, 768)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout_principal = QVBoxLayout(central_widget)

        # Aviso de chaves em atraso
        self.lblAlertaChaves = QLabel()
        self.lblAlertaChaves.setStyleSheet(
            "QLabel { background-color: #ffcc00; color: #000; font-weight: bold; padding: 8px; font-size: 12pt; }"
        )
        self.lblAlertaChaves.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblAlertaChaves.hide()
        layout_principal.addWidget(self.lblAlertaChaves)
        layout_principal.addSpacing(12)

        # Relógio
        topo_layout = QHBoxLayout()

        self.label_hora = QLabel()
        self.label_hora.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_hora.setStyleSheet(
            "QLabel { background-color: #f8f9fa; color: #212529; "
            "font-size: 24px; font-weight: 500; padding: 10px 14px; "
            "border: 1px solid #dee2e6; border-radius: 4px; }"
        )
        topo_layout.addWidget(self.label_hora)

        topo_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        topo_layout.addItem(topo_spacer)

        layout_principal.addLayout(topo_layout)

        # Timers
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizar_hora)
        self.timer.start(1000)
        self.atualizar_hora()

        self.timer_chaves_atraso = QTimer(self)
        self.timer_chaves_atraso.timeout.connect(self.verificar_chaves_atraso)
        self.timer_chaves_atraso.start(30000)
        self.verificar_chaves_atraso()

        # Logo
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        caminho_logo = caminho_recurso(config.APP_LOGO_PATH)
        pix = QPixmap(caminho_logo)
        if not pix.isNull():
            pix = pix.scaledToHeight(120, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pix)
        else:
            self.logo_label.setText(config.APP_NAME)
            self.logo_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        layout_principal.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Abas
        self.tabs = QTabWidget()
        layout_principal.addWidget(self.tabs)

        # Barra inferior
        bottom_bar_layout = QHBoxLayout()

        self.label_usuario_bottom = QLabel(f"Utilizador: {self.user_nome} ({self.user_login})")
        self.label_usuario_bottom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_usuario_bottom.setStyleSheet("color: #555; padding: 4px;")
        bottom_bar_layout.addWidget(self.label_usuario_bottom)

        bottom_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        bottom_bar_layout.addItem(bottom_spacer)

        self.btn_sobre = QPushButton("Sobre")
        self.btn_sobre.clicked.connect(self.mostrar_sobre)
        self.btn_sobre.setStyleSheet(
            f"QPushButton {{ background-color: {config.COLOR_BTN_LARANJA}; "
            f"color: {config.COLOR_BTN_TEXTO_ESCURO}; padding: 6px 12px; border-radius: 6px; }}"
        )
        bottom_bar_layout.addWidget(self.btn_sobre)

        self.btn_logout = QPushButton("Logout")
        self.btn_logout.clicked.connect(self.confirmar_logout)
        self.btn_logout.setStyleSheet(
            f"QPushButton {{ background-color: {config.COLOR_BTN_AZUL}; "
            f"color: {config.COLOR_BTN_TEXTO}; padding: 6px 12px; border-radius: 6px; }}"
        )
        bottom_bar_layout.addWidget(self.btn_logout)

        self.btn_sair = QPushButton("Sair")
        self.btn_sair.clicked.connect(self.sair)
        self.btn_sair.setStyleSheet(
            f"QPushButton {{ background-color: {config.COLOR_BTN_VERDE}; "
            f"color: {config.COLOR_BTN_TEXTO}; padding: 6px 12px; border-radius: 6px; }}"
        )
        bottom_bar_layout.addWidget(self.btn_sair)

        layout_principal.addLayout(bottom_bar_layout)

        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_label.setStyleSheet("QLabel { background-color: #dff0d8; color: #3c763d; padding: 6px; }")
        self.feedback_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.feedback_label.hide()
        layout_principal.addWidget(self.feedback_label)

        self.load_tabs()

    def atualizar_hora(self):
        self.label_hora.setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    def verificar_chaves_atraso(self):
        try:
            qtd = ha_chaves_em_atraso()
            if qtd > 0:
                self.lblAlertaChaves.setText(f"⚠️ HÁ {qtd} CHAVE(S) EM ATRASO! Verifique a devolução.")
                self.lblAlertaChaves.show()
            else:
                self.lblAlertaChaves.hide()
        except Exception:
            self.lblAlertaChaves.hide()
            logger.exception("Erro ao verificar chaves em atraso")

    def mostrar_sobre(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Sobre")
        msg.setText(
            f"{config.APP_NAME}\nVersão: {config.APP_VERSION}\n{config.APP_COMPANY}"
        )
        caminho_logo = caminho_recurso(config.APP_LOGO_PATH)
        pix = QPixmap(caminho_logo)
        if not pix.isNull():
            pix = pix.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
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
        self.mov_tab = self.rel_tab = self.util_tab = self.admin_tab = self.logs_tab = None

        # Aba Movimentações — todos veem
        try:
            self.mov_tab = MovimentacoesTab(dash_main_ref=self)
            self.tabs.addTab(self.mov_tab, "Movimentações")
        except Exception as e:
            import traceback
            detalhes = traceback.format_exc()
            print(f"ERRO COMPLETO:\n{detalhes}")
            QMessageBox.critical(self, "Erro",
                                 f"Falha ao carregar aba Movimentações:\n{str(e)}\n\nVerifique o terminal!")

        # Aba Relatórios — todos veem
        try:
            self.rel_tab = RelatoriosTab()
            self.tabs.addTab(self.rel_tab, "Relatórios")
        except Exception:
            logger.exception("Erro na aba Relatórios")
            QMessageBox.critical(self, "Erro", "Falha ao carregar aba Relatórios.")

        # ✅ Aba de ADMIN — só administradores veem
        if self.eh_admin:
            # Aba Utilizadores ✅
            try:
                self.util_tab = UtilizadoresTab()
                self.tabs.addTab(self.util_tab, "Utilizadores")
            except Exception as e:
                import traceback
                detalhes = traceback.format_exc()
                print(f"ERRO Utilizadores:\n{detalhes}")
                QMessageBox.warning(self, "Aviso",
                                    f"Falha ao carregar aba Utilizadores:\n{str(e)}\n\nVerifique o terminal.")

            # Aba Administração
            try:
                dados_admin = {
                    "login": self.user_login,
                    "nome": self.user_nome,
                    "is_admin": True
                }
                self.admin_tab = AdminTab(dados_admin)
                self.tabs.addTab(self.admin_tab, "Administração")
            except Exception as e:
                logger.exception("Erro na aba Administração")
                QMessageBox.warning(self, "Erro", f"Falha ao carregar Administração:\n{e}")

            # Aba Logs
            try:
                self.logs_tab = LogViewerTab()
                self.tabs.addTab(self.logs_tab, "Logs")
            except Exception:
                logger.exception("Erro na aba Logs")
                QMessageBox.warning(self, "Aviso", "Falha ao carregar aba Logs.")

    def confirmar_logout(self):
        resp = QMessageBox.question(
            self,
            "Confirmar Saída",
            "Deseja realmente encerrar a sessão?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            self._logout_realizado = True
            if self.on_logout:
                self.on_logout()
            else:
                self.close()

    def sair(self):
        QApplication.instance().quit()

    def closeEvent(self, event):
        for nome_timer in ["timer", "timer_chaves_atraso"]:
            if hasattr(self, nome_timer):
                getattr(self, nome_timer).stop()
        super().closeEvent(event)