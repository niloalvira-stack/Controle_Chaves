from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget
)

from admin.usuarios import UsuariosTab
from admin.predios import PrediosTab
from admin.anexos import AnexosTab
from admin.salas import SalasTab


class AdminTab(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {}

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.usuarios_tab = UsuariosTab()
        self.salas_tab = SalasTab(current_user=self.current_user)
        self.predios_tab = PrediosTab()
        self.anexos_tab = AnexosTab()

        self.tabs.addTab(self.usuarios_tab, "Usuários")
        self.tabs.addTab(self.salas_tab, "Salas")
        self.tabs.addTab(self.predios_tab, "Prédios")
        self.tabs.addTab(self.anexos_tab, "Anexos")
