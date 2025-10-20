from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from admin.usuarios import UsuariosTab
from admin.predios import PrediosTab
from admin.anexos import AnexosTab
from admin.salas import SalasTab

class AdminTab(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.tabs.addTab(UsuariosTab(), "Usuários")
        self.tabs.addTab(SalasTab(), "Salas")
        self.tabs.addTab(PrediosTab(), "Prédios")
        self.tabs.addTab(AnexosTab(), "Anexos")
