import sys
from PyQt5.QtWidgets import QApplication

from autenticacao import session_manager
from autenticacao.login_window import LoginWindow
from interface.dash_main import DashMain
from utils.utils_log import log_acao


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)

        # ESTILO GLOBAL (padrão Movimentações) PARA TODOS OS QPushButton
        self.app.setStyleSheet("""
        QPushButton {
            padding: 10px 24px;
            min-height: 34px;
            min-width: 140px;
            border-radius: 6px;
            border: 1px solid #888;
            font-weight: 500;
        }

        QPushButton#btnEscolherSala {
            background-color: #eeeeee;
        }
        QPushButton#btnEscolherSala:hover {
            background-color: #f5f5f5;
        }

        QPushButton#btnRetirar {
            background-color: #2e7d32;
            color: white;
            border: 1px solid #1b5e20;
        }
        QPushButton#btnRetirar:hover {
            background-color: #388e3c;
        }
        QPushButton#btnRetirar:pressed {
            background-color: #1b5e20;
        }

        QPushButton#btnDevolver {
            background-color: #1565c0;
            color: white;
            border: 1px solid #0d47a1;
        }
        QPushButton#btnDevolver:hover {
            background-color: #1976d2;
        }
        QPushButton#btnDevolver:pressed {
            background-color: #0d47a1;
        }

        QPushButton#btnFiltrar,
        QPushButton#btnVerificarPendencias {
            background-color: #f9a825;
            color: #333333;
            border: 1px solid #f57f17;
        }
        QPushButton#btnFiltrar:hover,
        QPushButton#btnVerificarPendencias:hover {
            background-color: #fbc02d;
        }
        QPushButton#btnFiltrar:pressed,
        QPushButton#btnVerificarPendencias:pressed {
            background-color: #f57f17;
        }
        """)

        self.login_window = None
        self.dash_main = None

    def show_login(self):
        print("DEBUG: show_login chamado")
        self.login_window = LoginWindow(on_login_success=self.on_login_success)
        self.login_window.show()

    def on_login_success(self, user_dict):
        print("DEBUG: on_login_success em MainApp chamado:", user_dict)

        # auditoria de login
        try:
            login = user_dict.get("login", "")
        except Exception:
            login = ""
        log_acao(
            action="login",
            user=login,
            resource="sistema",
            status="success",
            details="Login efetuado com sucesso",
        )

        # garante sessão carregada, se por algum motivo não estiver
        if not session_manager.current_user:
            session_manager.login(login)

        if self.login_window is not None:
            self.login_window.close()
            self.login_window = None

        print("DEBUG: criando DashMain")
        self.dash_main = DashMain(on_logout=self.handle_logout)
        self.dash_main.showMaximized()

    def handle_logout(self):
        print("DEBUG: handle_logout chamado")
        try:
            # auditoria de logout
            usuario = session_manager.current_user["login"] if session_manager.current_user else ""
            log_acao(
                action="logout",
                user=usuario,
                resource="sistema",
                status="success",
                details="Logout efetuado pelo usuário",
            )
        except Exception:
            pass

        try:
            session_manager.logout()
        except Exception:
            pass

        if self.dash_main is not None:
            self.dash_main.close()
            self.dash_main = None

        self.show_login()

    def run(self):
        self.show_login()
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()
