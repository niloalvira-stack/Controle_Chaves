import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QMessageBox
)
from admin.admin import AdminTab
from autenticacao.login_window import LoginWindow
from controle.movimentacoes import MovimentacoesTab
from autenticacao.session import is_admin

# IMPORTAÇÃO DAS ABAS DE RELATÓRIOS
from relatorios.relatorios_geral_tab import RelatoriosGeralTab
from relatorios.relatorio_periodo_tab import RelatorioPorPeriodoTab
from relatorios.relatorio_usuario_tab import RelatorioPorUsuarioTab
from relatorios.relatorio_sala_tab import RelatorioPorSalaTab
from relatorios.relatorio_pendencias_tab import RelatorioPendenciasTab



class DashMain(QMainWindow):
    def __init__(self):
        print("Entrando no construtor DashMain")
        super().__init__()
        self.setWindowTitle("Dashboard Controle de Chaves")
        self.resize(1000, 700)

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

        # Abas comuns a todos (inclui relatórios)
        print("DashMain: adicionando RelatoriosGeralTab")
        self.tabs.addTab(RelatoriosGeralTab(), "Relatório Geral")
        self.tabs.addTab(RelatorioPorPeriodoTab(), "Relatório por Período")
        self.tabs.addTab(RelatorioPorUsuarioTab(), "Relatório por Usuário")
        self.tabs.addTab(RelatorioPorSalaTab(), "Relatório por Sala")
        self.tabs.addTab(RelatorioPendenciasTab(), "Pendências")

        # Aba administração restrita para admin
        if is_admin():
            print("DashMain: usuário é admin, adicionando AdminTab")
            self.tabs.addTab(AdminTab(), "Administração")
        else:
            QMessageBox.information(self, "Restrição", "A aba Administração é acessível apenas para administradores.")

    def sair(self):
        print("DashMain: sair chamado, janela fechada")
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashMain()
    window.show()
    sys.exit(app.exec_())
