# relatorios/relatorios_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from .relatorio_geral import RelatorioGeralTab
from .relatorio_pendencias_tab import RelatorioPendenciasTab
from .relatorio_periodo_tab import RelatorioPorPeriodoTab
from .relatorio_sala_tab import RelatorioPorSalaTab
from .relatorio_usuario_tab import RelatorioPorUsuarioTab
from relatorios.relatorios_graficos import RelatorioGraficosTab


class RelatoriosTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.addTab(RelatorioGeralTab(), "Geral")
        self.tabs.addTab(RelatorioPendenciasTab(), "Pendências")
        self.tabs.addTab(RelatorioPorPeriodoTab(), "Por Período")
        self.tabs.addTab(RelatorioPorSalaTab(), "Por Sala")
        self.tabs.addTab(RelatorioPorUsuarioTab(), "Por Usuário")
        self.tabs.addTab(RelatorioGraficosTab(), "📊 Gráficos")