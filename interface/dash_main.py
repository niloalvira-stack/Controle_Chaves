import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QMessageBox,
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)

from admin.admin import AdminTab
from autenticacao.login_window import LoginWindow
from autenticacao.session import session_manager, is_admin




class SomeCommonWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Conteúdo das movimentações"))
        self.setLayout(layout)

class AdminWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Painel administrativo"))
        self.setLayout(layout)

class DashMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard Controle de Chaves")
        self.resize(800, 600)

        main_layout = QVBoxLayout()

        # Área para botão sair
        button_layout = QHBoxLayout()
        self.btn_sair = QPushButton("Sair")
        self.btn_sair.clicked.connect(self.sair)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_sair)
        main_layout.addLayout(button_layout)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Container principal que segura o layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.load_tabs()

    def load_tabs(self):
        self.tabs.addTab(SomeCommonWidget(), "Movimentações")

        if is_admin():
            self.tabs.addTab(AdminTab(), "Administração")

        else:
            QMessageBox.information(
                self, "Restrição",
                "A aba Administração é acessível apenas para administradores."
            )

    def sair(self):
        self.close()

class MainApp:
    def __init__(self):
        print("Inicializando QApplication...")
        self.app = QApplication(sys.argv)
        print("Criando janela de login...")
        self.login_window = LoginWindow(self.on_login_success)
        self.dash_main = None

    def on_login_success(self, user):
        print(f"Login bem-sucedido para {user['login']}")
        session_manager.login(user["login"], user["is_admin"])
        self.dash_main = DashMain()
        self.dash_main.show()
        self.login_window.close()

    def run(self):
        self.login_window.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()
