import sys
import os

from PyQt5.QtWidgets import QApplication

from autenticacao import session_manager
from autenticacao.login_window import LoginWindow
from interface.dash_main import DashMain


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = None
        self.dash_main = None

    def run(self):
        # Garante diretório de trabalho correto
        base_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(base_dir)

        self.show_login()
        sys.exit(self.app.exec_())

    # ------------------------------------------------------------
    # Fluxo de login
    # ------------------------------------------------------------
    def show_login(self):
        self.login_window = LoginWindow(on_login_success=self.on_login_success)
        self.login_window.show()

    def on_login_success(self, user_dict):
        """
        Chamado pelo LoginWindow quando a senha é validada.
        user_dict é o dicionário retornado de get_user_by_login(login).
        """
        login = user_dict["login"]

        # Cria / atualiza sessão global com base no login
        ok = session_manager.login(login)
        if not ok:
            # Se por algum motivo não conseguir carregar o usuário na sessão,
            # apenas volta para a tela de login.
            self.login_window.show()
            return

        # Abre painel principal já com a sessão populada
        # Passando callback de logout
        self.dash_main = DashMain(on_logout=self.handle_logout)
        self.dash_main.showMaximized()
        self.login_window.close()
        self.login_window = None

    def handle_logout(self):
        """
        Chamado pelo DashMain quando o usuário clica em Logout.
        Limpa a sessão, fecha o painel e volta para a tela de login.
        """
        session_manager.logout()

        if self.dash_main:
            self.dash_main.close()
            self.dash_main = None

        self.show_login()  # e nada mais aqui


if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()
