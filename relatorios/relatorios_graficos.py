# relatorios/relatorios_graficos.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from .base_relatorio_tab import BaseRelatorioTab
from utils.ui_buttons import criar_botao_padrao


class RelatorioGraficosTab(BaseRelatorioTab):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        topo = QHBoxLayout()
        self.btn_atualizar = criar_botao_padrao(
            "Atualizar gráficos",
            role="primary",
            slot=self.load_relatorio
        )
        topo.addWidget(self.btn_atualizar)
        topo.addStretch()
        layout.addLayout(topo)

        self.figure = Figure(figsize=(9, 5), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        layout.addWidget(self.canvas)

        self._render_empty_chart()

    def _render_empty_chart(self):
        self.ax.clear()
        self.ax.set_title("Movimentações por Sala")
        self.ax.set_xlabel("Sala")
        self.ax.set_ylabel("Quantidade")
        self.ax.text(
            0.5, 0.5,
            "Nenhum dado carregado",
            ha="center", va="center",
            transform=self.ax.transAxes
        )
        self.canvas.draw_idle()

    def _query_base(self):
        return """
            SELECT COALESCE(NULLIF(TRIM(s.nome), ''), 'Sem nome') AS sala,
                   COUNT(*) AS total
            FROM movimentacoes m
            INNER JOIN salas s ON s.id = m.sala_id
            GROUP BY COALESCE(NULLIF(TRIM(s.nome), ''), 'Sem nome')
            ORDER BY total DESC, sala
        """

    def load_relatorio(self):
        if self._carregando:
            return

        self.btn_atualizar.setEnabled(False)
        self._iniciar_query(self._query_base(), on_loaded=self._on_loaded)

    def _on_loaded(self, rows):
        self._rows_cache = rows or []
        self._plotar_grafico(self._rows_cache)

    def _on_finished(self):
        super()._on_finished()
        self.btn_atualizar.setEnabled(True)

    def _plotar_grafico(self, rows):
        self.ax.clear()

        if not rows:
            self._render_empty_chart()
            return

        salas = [str(row[0]) for row in rows]
        totais = [int(row[1]) for row in rows]

        bars = self.ax.bar(salas, totais, color="#1976d2")

        self.ax.set_title("Movimentações por Sala")
        self.ax.set_xlabel("Sala")
        self.ax.set_ylabel("Quantidade")
        self.ax.tick_params(axis="x", labelrotation=35)

        for label in self.ax.get_xticklabels():
            label.set_ha("right")

        for bar, total in zip(bars, totais):
            self.ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                str(total),
                ha="center",
                va="bottom"
            )

        self.figure.tight_layout()
        self.canvas.draw_idle()

    def _on_error(self, msg):
        QMessageBox.critical(self, "Erro", f"Erro ao carregar gráficos:\n{msg}")
        self._render_empty_chart()