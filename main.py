import sys
import os

from PyQt5.QtWidgets import QApplication

from autenticacao import session_manager
from autenticacao.login_window import LoginWindow
from interface.dash_main import DashMain
# from database_module import inicializar_banco  # não precisa mais chamar aqui


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = None
        self.dash_main = None

    def run(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(base_dir)

        self.show_login()
        sys.exit(self.app.exec_())

    def show_login(self):
        self.login_window = LoginWindow(on_login_success=self.on_login_success)
        self.login_window.show()

    def on_login_success(self, user_dict):
        login = user_dict["login"]

        ok = session_manager.login(login)
        if not ok:
            self.login_window.show()
            return

        self.dash_main = DashMain(on_logout=self.handle_logout)
        self.dash_main.showMaximized()
        self.login_window.close()
        self.login_window = None

    def handle_logout(self):
        session_manager.logout()

        if self.dash_main:
            self.dash_main.close()
            self.dash_main = None

        self.show_login()


if __name__ == "__main__":
    # inicializar_banco()  # REMOVIDO para Postgres

    main_app = MainApp()
    main_app.run()
