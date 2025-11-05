import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox
from admin.admin import AdminTab
from autenticacao.login_window import LoginWindow
from controle.movimentacoes import MovimentacoesTab
from autenticacao.session import is_admin

print("INICIO: dash_main.py")

class DashMain(QMainWindow):
    def __init__(self):
        print("Entrando no construtor DashMain")
        super().__init__()
        self.setWindowTitle("Dashboard Controle de Chaves")
        self.resize(800, 600)

        main_layout = QVBoxLayout()

        button_layout = QHBoxLayout()
        self.btn_sair = QPushButton("Sair")
        self.btn_sair.clicked.connect(self.sair)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_sair)
        main_layout.addLayout(button_layout)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.load_tabs()

    def load_tabs(self):
        print("DashMain: adicionando MovimentacoesTab")
        self.tabs.addTab(MovimentacoesTab(), "Movimentações")
        if is_admin():
            print("DashMain: usuário é admin, adicionando AdminTab")
            self.tabs.addTab(AdminTab(), "Administração")
        else:
            QMessageBox.information(self, "Restrição", "A aba Administração é acessível apenas para administradores.")

    def sair(self):
        print("DashMain: sair chamado, janela fechada")
        self.close()
