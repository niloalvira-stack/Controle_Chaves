# main.py
import sys
import traceback

from PyQt6.QtWidgets import QApplication, QDialog

from autenticacao.login_window import LoginWindow
from autenticacao.session import session_manager
from interface.dash_main import DashMain
from utils.utils_log import log_acao
from pathlib import Path


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = None
        self.dash_main = None

        self.carregar_qss_global()

    def carregar_qss_global(self):
        try:
            qss_path = Path(__file__).parent / "styles" / "app.qss"
            if qss_path.exists():
                self.app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Erro ao carregar QSS global: {e}")

    def mostrar_login(self):
        self.login_window = LoginWindow()

        if self.login_window.exec() == QDialog.DialogCode.Accepted:
            self.abrir_dashboard()
        else:
            self.app.quit()

    def abrir_dashboard(self):
        self.dash_main = DashMain(on_logout=self.fazer_logout)
        self.dash_main.show()

    def fazer_logout(self):
        login_atual = None

        try:
            user_atual = getattr(session_manager, "current_user", None)

            if isinstance(user_atual, dict):
                login_atual = user_atual.get("login") or user_atual.get("nome")
            else:
                login_atual = getattr(user_atual, "login", None) or getattr(user_atual, "nome", None)

            if not login_atual and hasattr(session_manager, "get_user_login"):
                login_atual = session_manager.get_user_login()

            if login_atual:
                log_acao(
                    action="Logout realizado",
                    user=login_atual,
                    resource="autenticacao",
                    status="success",
                    details="encerramento_de_sessao",
                )
        except Exception:
            print(traceback.format_exc())

        try:
            if hasattr(session_manager, "logout"):
                session_manager.logout()
        except Exception:
            print(traceback.format_exc())

        if self.dash_main is not None:
            self.dash_main.close()
            self.dash_main = None

        self.mostrar_login()
    def run(self):
        self.mostrar_login()
        sys.exit(self.app.exec())


if __name__ == "__main__":
    MainApp().run()