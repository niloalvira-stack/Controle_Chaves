from datetime import datetime

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from autenticacao.helpers_autenticacao import get_db_connection


def formatar_data_br_dia(valor):
    if not valor:
        return ""
    try:
        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y")
        return datetime.strptime(str(valor), "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(valor)


class RelatorioGraficosTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Relatórios Gráficos")
        layout = QVBoxLayout(self)

        self.fig = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.gerar_graficos()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.gerar_graficos)
        self.timer.start(30000)

    def _buscar_dados(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                DATE(data_retirada) AS dia,
                COUNT(*) AS total
            FROM movimentacoes
            WHERE data_retirada IS NOT NULL
            GROUP BY DATE(data_retirada)
            ORDER BY DATE(data_retirada)
        """)

        rows = cursor.fetchall()
        conn.close()

        dias = [r[0] for r in rows]
        totais = [r[1] for r in rows]
        return dias, totais

    def gerar_graficos(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        dias, totais = self._buscar_dados()

        if not dias:
            ax.text(0.5, 0.5, "Sem dados de movimentações.",
                    ha="center", va="center", transform=ax.transAxes)
        else:
            labels = [formatar_data_br_dia(d) for d in dias]
            x = range(len(dias))

            ax.bar(x, totais)
            ax.set_xticks(list(x))
            ax.set_xticklabels(labels, rotation=45, ha="right")
            ax.set_ylabel("Qtde de movimentações")
            ax.set_xlabel("Data de retirada")
            ax.set_title("Movimentações por dia")
            self.fig.tight_layout()

        self.canvas.draw()