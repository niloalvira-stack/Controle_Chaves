from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from .relatorio_geral import RelatorioGeralTab
from .relatorio_pendencias_tab import RelatorioPendenciasTab
from .relatorio_periodo_tab import RelatorioPorPeriodoTab
from .relatorio_sala_tab import RelatorioPorSalaTab
from .relatorio_usuario_tab import RelatorioPorUsuarioTab
from .relatorios_graficos import RelatorioGraficosTab


class RelatoriosTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tab_geral = RelatorioGeralTab()
        self.tab_pendencias = RelatorioPendenciasTab()
        self.tab_periodo = RelatorioPorPeriodoTab()
        self.tab_sala = RelatorioPorSalaTab()
        self.tab_usuario = RelatorioPorUsuarioTab()
        self.tab_graficos = RelatorioGraficosTab()

        self.tabs.addTab(self.tab_geral, "Geral")
        self.tabs.addTab(self.tab_pendencias, "Pendências")
        self.tabs.addTab(self.tab_periodo, "Por Período")
        self.tabs.addTab(self.tab_sala, "Por Sala")
        self.tabs.addTab(self.tab_usuario, "Por Utilizador")
        self.tabs.addTab(self.tab_graficos, "📊 Gráficos")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        self._on_tab_changed(self.tabs.currentIndex())

    def _on_tab_changed(self, index):
        widget = self.tabs.widget(index)
        if widget and hasattr(widget, "carregar_inicial"):
            widget.carregar_inicial()