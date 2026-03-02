from admin.utilizadores_tab import UtilizadoresTab

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
)

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer

from admin.admin import AdminTab
from admin.log_viewer_tab import LogViewerTab

from autenticacao import session_manager, get_current_user, is_admin

from config import (
    APP_NAME,
    APP_VERSION,
    APP_COMPANY,
    APP_DEVELOPER,
    APP_COPYRIGHT,
    APP_LOGO_PATH,
)
from controle.movimentacoes import MovimentacoesTab
from relatorios.relatorios_tab import RelatoriosTab


class DashMain(QMainWindow):
    def __init__(self, on_logout=None):
        super().__init__()
        print("DashMain.__init__ chamado")

        self.on_logout = on_logout

        info_user = get_current_user()
        print("DEBUG get_current_user em DashMain:", info_user)
        print("DEBUG session_manager.is_admin:", session_manager.is_admin)
        print("DEBUG is_admin():", is_admin())

        self.setWindowTitle(f"{APP_NAME} - Painel Principal")
        self.resize(1200, 800)

        # Abas principais
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)

        # Widget central e layout principal
        central = QWidget()
        layout_principal = QVBoxLayout(central)

        # ===== Faixa superior: relógio (esq) + logo (centro) =====
        top_bar = QHBoxLayout()

        # Relógio à esquerda com estilo customizado
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.clock_label.setStyleSheet("""
            QLabel {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 20px;
                font-weight: bold;
                color: #00FF00;
                background-color: #000000;
                padding: 6px 12px;
                border-radius: 6px;
                border: 1px solid #00AA00;
            }
        """)
        top_bar.addWidget(self.clock_label)

        # Stretch para empurrar o logo para o centro visual
        top_bar.addStretch()

        # Logo centralizado
        self.logo_label = QLabel()
        pix = QPixmap(APP_LOGO_PATH)
        if not pix.isNull():
            pix = pix.scaled(260, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pix)
        self.logo_label.setAlignment(Qt.AlignCenter)
        top_bar.addWidget(self.logo_label)

        # Stretch à direita para manter o logo no centro
        top_bar.addStretch()

        layout_principal.addLayout(top_bar)

        # Abas logo abaixo do topo
        layout_principal.addWidget(self.tabs)

        # ===== Barra inferior: infos + botões =====
        bottom_bar = QHBoxLayout()

        bottom_bar.addStretch()

        self.label_usuario = QLabel()
        self.label_hora = QLabel()

        # Label de feedback abaixo da barra inferior
        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setStyleSheet("""
            QLabel {
                background-color: #4caf50;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
            }
        """)
        self.feedback_label.hide()
        layout_principal.addWidget(self.feedback_label)


        bottom_bar.addWidget(self.label_usuario)
        bottom_bar.addSpacing(20)
        bottom_bar.addWidget(self.label_hora)
        bottom_bar.addSpacing(20)

        btn_sobre = QPushButton("Sobre")
        btn_logout = QPushButton("Logout")
        btn_logout.setObjectName("btnLogout")
        btn_sair = QPushButton("Sair")

        btn_sobre.clicked.connect(self.mostrar_sobre)
        btn_logout.clicked.connect(self.logout)
        btn_sair.clicked.connect(self.sair)

        bottom_bar.addWidget(btn_sobre)
        bottom_bar.addWidget(btn_logout)
        bottom_bar.addWidget(btn_sair)

        layout_principal.addLayout(bottom_bar)

        self.setCentralWidget(central)

        # Estilos de botões
        self.setStyleSheet("""
            QPushButton {
                padding: 10px 24px;
                min-height: 34px;
                min-width: 140px;
                border-radius: 6px;
                border: 1px solid #888;
                font-weight: 500;
            }
            QPushButton#btnLogout {
                background-color: #f9a825;
                color: #333333;
                border: 1px solid #f57f17;
            }
            QPushButton#btnLogout:hover {
                background-color: #fbc02d;
            }
            QPushButton#btnLogout:pressed {
                background-color: #f57f17;
            }
        """)

        # Status bar para mensagens automáticas
        self.status = self.statusBar()
        self.status.showMessage("Pronto")

        # Infos iniciais (parte inferior)
        self.atualizar_informacoes_usuario()

        # Relógio superior (digital, lado esquerdo)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.atualizar_relogio)
        self.clock_timer.start(1000)  # 1 segundo
        self.atualizar_relogio()

        # Carregar abas
        self.load_tabs()

    # ===== Atualizações de usuário / hora inferior =====
    def atualizar_informacoes_usuario(self):
        user = get_current_user()
        print("DEBUG user dict:", user)
        if user:
            nome = (
                    user.get("nome_real")
                    or user.get("nome")
                    or user.get("usuario")
                    or "Usuário"
            )
            perfil = "Administrador" if user.get("is_admin") else "Usuário comum"
            self.label_usuario.setText(f"{nome} - {perfil}")
        else:
            self.label_usuario.setText("Nenhum usuário logado")

        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.label_hora.setText(f"{agora}")

    # ===== Relógio no topo (lado esquerdo) =====
    def atualizar_relogio(self):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.clock_label.setText(agora)

    # ===== Abas =====
    def load_tabs(self):
        print("Entrou em load_tabs()")
        self.tabs.clear()

        self.mov_tab = None
        self.rel_tab = None
        self.util_tab = None

        # Movimentações
        try:
            self.mov_tab = MovimentacoesTab()
            self.tabs.addTab(self.mov_tab, "Movimentações")
            print("  Aba Movimentações adicionada.")
        except Exception as e:
            print(f"ERRO ao criar MovimentacoesTab: {e}")
            QMessageBox.critical(self, "Erro", f"Falha ao carregar aba Movimentações:\n{e}")

        # Relatórios
        try:
            self.rel_tab = RelatoriosTab()
            self.tabs.addTab(self.rel_tab, "Relatórios")
            print("  Aba Relatórios adicionada.")
        except Exception as e:
            print(f"ERRO ao criar RelatoriosTab: {e}")
            QMessageBox.critical(self, "Erro", f"Falha ao carregar aba Relatórios:\n{e}")

        # Utilizadores
        try:
            self.util_tab = UtilizadoresTab(movimentacoes_tab=self.mov_tab)
            self.tabs.addTab(self.util_tab, "Utilizadores")
            print("  Aba Utilizadores adicionada.")
        except Exception as e:
            print(f"ERRO ao criar UtilizadoresTab: {e}")
            QMessageBox.critical(self, "Erro", f"Falha ao carregar aba Utilizadores:\n{e}")

        # Admin / Logs (somente admin)
        try:
            debug_admin = is_admin()
            print("  DEBUG is_admin() em load_tabs:", debug_admin)

            if debug_admin:
                self.tabs.addTab(AdminTab(), "Administração")
                self.tabs.addTab(LogViewerTab(), "Logs do Sistema")
            else:
                print("  Usuário não é admin; abas Administração/Logs ocultas.")
        except Exception as e:
            import traceback
            print("ERRO ao verificar/admin abas:", e)
            traceback.print_exc()
            QMessageBox.warning(
                self,
                "Aviso",
                f"Falha ao verificar permissões de administrador:\n{e}",
            )

    # ===== Sobre / Logout / Sair =====
    def mostrar_sobre(self):
        QMessageBox.information(
            self,
            "Sobre",
            f"{APP_NAME} v{APP_VERSION}\n{APP_COMPANY}\n{APP_DEVELOPER}\n{APP_COPYRIGHT}",
        )

    def logout(self):
        if self.on_logout:
            self.on_logout()
        else:
            try:
                session_manager.logout()
            except Exception:
                pass
            self.close()

    def sair(self):
        QApplication.instance().quit()

    def show_operation_done(self, message="Operação concluída com sucesso."):
        self.feedback_label.setText(message)
        self.feedback_label.show()

        # some sozinho após 4 segundos
        QTimer.singleShot(4000, self.feedback_label.hide)


    def show_status_message(self, message):
        self.show_operation_done(message)
