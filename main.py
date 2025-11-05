import sys
from PyQt5.QtWidgets import QApplication
from autenticacao.login_window import LoginWindow
from interface.dash_main import DashMain
from autenticacao.session import session_manager  # Import ajustado para a pasta autenticacao
from database_init import init_database
init_database()


class MainApp:
    def __init__(self):
        print("Inicializando QApplication...")
        self.app = QApplication(sys.argv)
        print("Criando janela de login...")
        self.login_window = LoginWindow(self.on_login_success)
        self.dash_main = None

    def on_login_success(self, user):
        print(f"Login bem-sucedido para {user['login']}")
        session_manager.login(user["login"], user["is_admin"])  # acesso direto via colchetes
        self.dash_main = DashMain()
        self.dash_main.show()
        self.login_window.close()

    def run(self):
        self.login_window.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()
