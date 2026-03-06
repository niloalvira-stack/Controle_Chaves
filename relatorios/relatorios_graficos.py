from datetime import datetime

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from database_module import get_connection


def formatar_data_br_dia(valor):
    if not valor:
        return ""
    try:
        if isinstance(valor, datetime):
            return valor.strftime("%d%m%Y")   # DDMMAAAA
        return datetime.strptime(valor, "%Y-%m-%d").strftime("%d%m%Y")
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

        self.setLayout(layout)

        self.gerar_graficos()

        # Atualiza a cada 30 segundos
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.gerar_graficos)
        self.timer.start(30000)

    def _buscar_dados(self):
        """
        Quantidade de movimentações por dia (data_retirada).
        """
        conn = get_connection()
        if conn is None:
            return [], []

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
        rows = cursor.fetchall()  # RealDictRow
        conn.close()

        dias = [row["dia"] for row in rows]
        totais = [row["total"] for row in rows]
        return dias, totais

    def gerar_graficos(self):
        """
        Atualiza o gráfico com os dados atuais.
        """
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
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha="right")
            ax.set_ylabel("Qtde de movimentações")
            ax.set_xlabel("Data de retirada")
            ax.set_title("Movimentações por dia")

            self.fig.tight_layout()

        self.canvas.draw()
