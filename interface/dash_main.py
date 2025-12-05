# interface/dash_main.py

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QMessageBox, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from datetime import datetime

from config import (
    APP_NAME, APP_VERSION, APP_DEVELOPER,
    APP_COMPANY, APP_COPYRIGHT, APP_LOGO_PATH
)

from controle.movimentacoes import listar_movimentacoes, MovimentacoesTab
from autenticacao.session import get_current_user, is_admin, session_manager
from autenticacao.login_window import LoginWindow

from relatorios.relatorios_geral_tab import RelatoriosGeralTab
from relatorios.relatorio_periodo_tab import RelatorioPorPeriodoTab
from relatorios.relatorio_usuario_tab import RelatorioPorUsuarioTab
from relatorios.relatorio_sala_tab import RelatorioPorSalaTab
from relatorios.relatorio_pendencias_tab import RelatorioPendenciasTab
from relatorios.relatorios_graficos import RelatorioGraficosTab

from admin.admin import AdminTab
from admin.log_viewer_tab import LogViewerTab


class DashMain(QMainWindow):
    def __init__(self):
        super().__init__()

        # título e ícone da janela
        self.setWindowTitle(f"{APP_NAME} - Dashboard")
        self.setWindowIcon(QIcon(APP_LOGO_PATH))
        self.resize(1000, 700)

        main_layout = QVBoxLayout()

        # ---- LOGO NO TOPO ----
        lbl_logo = QLabel()
        pixmap = QPixmap(APP_LOGO_PATH)
        if not pixmap.isNull():
            pixmap = pixmap.scaledToHeight(160, Qt.SmoothTransformation)
            lbl_logo.setPixmap(pixmap)
        lbl_logo.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(lbl_logo)

        # ---- PAINEL INFORMATIVO DO USUÁRIO ----
        info_user = get_current_user()  # {"login": ..., "nome": ..., "is_admin": ...}
        perfil = "Administrador" if info_user.get("is_admin", False) else "Usuário"

        lbl_usuario = QLabel(
            f"Usuário: {info_user.get('nome', '')} ({info_user.get('login', '')}) — Perfil: {perfil}"
        )
        lbl_data = QLabel(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        total_mov = len(listar_movimentacoes())
        lbl_total_mov = QLabel(f"Total de movimentações: {total_mov}")
        pendentes = [row for row in listar_movimentacoes() if row[5] == 'indisponível']
        lbl_pendencias = QLabel(f"Chaves não devolvidas: {len(pendentes)}")

        main_layout.addWidget(lbl_usuario)
        main_layout.addWidget(lbl_data)
        main_layout.addWidget(lbl_total_mov)
        main_layout.addWidget(lbl_pendencias)

        # ---- LINHA DE BOTÕES (Sobre / Logout / Sair) ----
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_sobre = QPushButton("Sobre")
        self.btn_sobre.setObjectName("btnSobre")
        self.btn_sobre.clicked.connect(self.mostrar_sobre)
        button_layout.addWidget(self.btn_sobre)

        self.btn_logout = QPushButton("Logout")
        self.btn_logout.setObjectName("btnLogout")
        self.btn_logout.clicked.connect(self.logout)
        button_layout.addWidget(self.btn_logout)

        self.btn_sair = QPushButton("Sair")
        self.btn_sair.setObjectName("btnSair")
        self.btn_sair.clicked.connect(self.sair)
        button_layout.addWidget(self.btn_sair)

        main_layout.addLayout(button_layout)

        # ---- ABAS PRINCIPAIS ----
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # ---- RODAPÉ COM VERSÃO / INSTITUIÇÃO / DESENVOLVEDOR ----
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        lbl_versao = QLabel(
            f"{APP_NAME} v{APP_VERSION} — {APP_COMPANY} — Desenvolvido por {APP_DEVELOPER}"
        )
        footer_layout.addWidget(lbl_versao)
        main_layout.addLayout(footer_layout)

        # ---- ESTILOS DOS BOTÕES ----
        self.setStyleSheet("""
            QPushButton {
                padding: 10px 24px;
                min-height: 34px;
                min-width: 120px;
                border-radius: 6px;
                border: 1px solid #888;
                font-weight: 500;
            }

            QPushButton#btnSobre {
                background-color: #1565c0;
                color: white;
                border: 1px solid #0d47a1;
            }
            QPushButton#btnSobre:hover {
                background-color: #1976d2;
            }
            QPushButton#btnSobre:pressed {
                background-color: #0d47a1;
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

            QPushButton#btnSair {
                background-color: #c62828;
                color: white;
                border: 1px solid #8e0000;
            }
            QPushButton#btnSair:hover {
                background-color: #d32f2f;
            }
            QPushButton#btnSair:pressed {
                background-color: #8e0000;
            }
        """)

        self.load_tabs()

    def load_tabs(self):
        # Movimentações
        self.tabs.addTab(MovimentacoesTab(), "Movimentações")

        # Relatórios (aba pai)
        relatorios_container = QWidget()
        relatorios_layout = QVBoxLayout(relatorios_container)

        relatorios_tabs = QTabWidget()
        relatorios_tabs.addTab(RelatoriosGeralTab(), "Geral")
        relatorios_tabs.addTab(RelatorioPorPeriodoTab(), "Por Período")
        relatorios_tabs.addTab(RelatorioPorUsuarioTab(), "Por Usuário")
        relatorios_tabs.addTab(RelatorioPorSalaTab(), "Por Sala")
        relatorios_tabs.addTab(RelatorioPendenciasTab(), "Pendências")
        relatorios_tabs.addTab(RelatorioGraficosTab(), "Gráficos")

        relatorios_layout.addWidget(relatorios_tabs)
        self.tabs.addTab(relatorios_container, "Relatórios")

        # Administração e Logs apenas para admin
        if is_admin():
            self.tabs.addTab(AdminTab(), "Administração")
            self.tabs.addTab(LogViewerTab(), "Logs do Sistema")
        else:
            QMessageBox.information(
                self,
                "Restrição",
                "A aba Administração é acessível apenas para administradores."
            )

    def mostrar_sobre(self):
        texto = (
            f"{APP_NAME}\n"
            f"Versão: {APP_VERSION}\n"
            f"Instituição: {APP_COMPANY}\n"
            f"Desenvolvedor: {APP_DEVELOPER}\n"
            f"{APP_COPYRIGHT}"
        )
        QMessageBox.information(self, "Sobre", texto)

    def logout(self):
        # encerra sessão e volta para a tela de login
        session_manager.logout()
        self.close()
        self.login_window = LoginWindow(self._on_login_success_again)
        self.login_window.show()

    def _on_login_success_again(self, user):
        # chamado quando logar de novo após logout
        session_manager.login(user["login"], user["is_admin"])
        novo = DashMain()
        novo.showMaximized()

    def sair(self):
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashMain()
    window.showMaximized()
    sys.exit(app.exec_())
