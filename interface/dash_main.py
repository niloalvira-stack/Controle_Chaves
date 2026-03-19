# interface/dash_main.py

from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QLabel,
    QApplication,
    QSpacerItem,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap

from admin.utilizadores_tab import UtilizadoresTab
from admin.admin import AdminTab
from admin.log_viewer_tab import LogViewerTab
from controle.movimentacoes import MovimentacoesTab
from relatorios.relatorios_tab import RelatoriosTab
from autenticacao import session_manager
import config


class DashMain(QMainWindow):
    def __init__(self, on_logout=None):
        super().__init__()

        print("DashMain.__init__ chamado")

        self.on_logout = on_logout

        user = session_manager.current_user
        if not user:
            self.user_login = "?"
            self.user_nome = "Desconhecido"
            self.user_is_admin = False
        else:
            self.user_login = getattr(user, "login", "?")
            self.user_nome = getattr(user, "nome", "Desconhecido")
            self.user_is_admin = getattr(user, "is_admin", False)

        self.setWindowTitle("Controle de Chaves - Painel Principal")
        self.resize(1024, 768)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout_principal = QVBoxLayout(central_widget)

        # TOPO - relógio
        topo_layout = QHBoxLayout()

        self.label_hora = QLabel()
        self.label_hora.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label_hora.setStyleSheet(
            "QLabel { background-color: black; color: #00ff00; "
            "font-size: 22px; font-weight: bold; padding: 4px 10px; }"
        )

        topo_layout.addWidget(self.label_hora)

        topo_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        topo_layout.addItem(topo_spacer)

        layout_principal.addLayout(topo_layout)

        # LOGO CENTRAL
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        pix = QPixmap(config.APP_LOGO_PATH)
        if not pix.isNull():
            pix = pix.scaledToHeight(120, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pix)
        else:
            self.logo_label.setText(config.APP_NAME)
            self.logo_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        layout_principal.addWidget(self.logo_label, alignment=Qt.AlignCenter)

        # TABS
        self.tabs = QTabWidget()
        layout_principal.addWidget(self.tabs)

        # BARRA INFERIOR: usuário + botões
        bottom_bar_layout = QHBoxLayout()

        self.label_usuario_bottom = QLabel(
            f"Utilizador logado: {self.user_nome} ({self.user_login})"
        )
        self.label_usuario_bottom.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label_usuario_bottom.setStyleSheet("color: #555555; padding: 4px;")
        bottom_bar_layout.addWidget(self.label_usuario_bottom)

        bottom_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        bottom_bar_layout.addItem(bottom_spacer)

        # Botão Sobre (laranja, como Filtrar/Verificar)
        self.btn_sobre = QPushButton("Sobre")
        self.btn_sobre.clicked.connect(self.mostrar_sobre)
        self.btn_sobre.setStyleSheet(
            f"QPushButton {{ background-color: {config.COLOR_BTN_LARANJA}; "
            f"color: {config.COLOR_BTN_TEXTO_ESCURO}; padding: 6px 12px; "
            f"border-radius: 6px; }}"
        )
        bottom_bar_layout.addWidget(self.btn_sobre)

        # Botão Logout (azul, como Devolver)
        self.btn_logout = QPushButton("Logout")
        self.btn_logout.clicked.connect(self.confirmar_logout)
        self.btn_logout.setStyleSheet(
            f"QPushButton {{ background-color: {config.COLOR_BTN_AZUL}; "
            f"color: {config.COLOR_BTN_TEXTO}; padding: 6px 12px; "
            f"border-radius: 6px; }}"
        )
        bottom_bar_layout.addWidget(self.btn_logout)

        # Botão Sair (verde, como Registrar Retirada)
        self.btn_sair = QPushButton("Sair")
        self.btn_sair.clicked.connect(self.sair)
        self.btn_sair.setStyleSheet(
            f"QPushButton {{ background-color: {config.COLOR_BTN_VERDE}; "
            f"color: {config.COLOR_BTN_TEXTO}; padding: 6px 12px; "
            f"border-radius: 6px; }}"
        )
        bottom_bar_layout.addWidget(self.btn_sair)

        layout_principal.addLayout(bottom_bar_layout)

        # FEEDBACK (barra inferior central)
        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setStyleSheet(
            "QLabel { background-color: #dff0d8; color: #3c763d; padding: 6px; }"
        )
        self.feedback_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.feedback_label.hide()

        layout_principal.addWidget(self.feedback_label)

        # Relógio timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizar_hora)
        self.timer.start(1000)
        self.atualizar_hora()

        self.mov_tab = None
        self.rel_tab = None
        self.util_tab = None
        self.admin_tab = None
        self.logs_tab = None

        self.load_tabs()

    def atualizar_hora(self):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.label_hora.setText(agora)

    def mostrar_sobre(self):
        info = (
            f"{config.APP_NAME}\n"
            f"Versão: {config.APP_VERSION}\n"
            f"Desenvolvedor: {config.APP_DEVELOPER}\n"
            f"Empresa: {config.APP_COMPANY}\n"
            f"{config.APP_COPYRIGHT}"
        )
        QMessageBox.information(self, "Sobre", info)

    def show_operation_done(self, message="Operação concluída com sucesso."):
        self.feedback_label.setText(message)
        self.feedback_label.show()
        QTimer.singleShot(4000, self.feedback_label.hide)

    def show_status_message(self, message):
        self.show_operation_done(message)

    def load_tabs(self):
        print("Entrou em load_tabs()")
        self.tabs.clear()

        self.mov_tab = None
        self.rel_tab = None
        self.util_tab = None
        self.admin_tab = None
        self.logs_tab = None

        try:
            self.mov_tab = MovimentacoesTab()
            self.tabs.addTab(self.mov_tab, "Movimentações")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar aba Movimentações:\n{e}")

        try:
            self.rel_tab = RelatoriosTab()
            self.tabs.addTab(self.rel_tab, "Relatórios")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar aba Relatórios:\n{e}")

        try:
            self.util_tab = UtilizadoresTab(movimentacoes_tab=self.mov_tab)
            self.tabs.addTab(self.util_tab, "Utilizadores")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar aba Utilizadores:\n{e}")

        try:
            if bool(self.user_is_admin):
                self.admin_tab = AdminTab()
                self.tabs.addTab(self.admin_tab, "Administração")

                self.logs_tab = LogViewerTab()
                self.tabs.addTab(self.logs_tab, "Logs")
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"Falha ao verificar permissões de administrador:\n{e}")

    def confirmar_logout(self):
        resp = QMessageBox.question(
            self,
            "Logout",
            "Deseja realmente terminar a sessão e voltar para a tela de login?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            try:
                session_manager.logout()
            except Exception:
                pass

            if self.on_logout:
                try:
                    self.on_logout()
                except Exception:
                    pass
            else:
                self.close()

    def closeEvent(self, event):
        try:
            session_manager.logout()
        except Exception:
            pass
        super().closeEvent(event)

    def sair(self):
        QApplication.instance().quit()
