import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

DB_NAME = "C:/Controle_Chaves/controle_chaves.db"


def formatar_data_br_dia(valor):
    if not valor:
        return ""
    try:
        # valor vem como 'YYYY-MM-DD'
        return datetime.strptime(valor, "%Y-%m-%d").strftime("%d/%m/%Y")
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

        # Botão é opcional; se não quiser, pode remover estas 3 linhas
        #self.btn_atualizar = QPushButton("Atualizar Gráficos")
        #self.btn_atualizar.clicked.connect(self.gerar_graficos)
        #layout.addWidget(self.btn_atualizar)

        self.setLayout(layout)

        # primeira geração
        self.gerar_graficos()

        # atualização em tempo quase real (a cada 5 segundos, por exemplo)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.gerar_graficos)
        self.timer.start(5000)

    def gerar_graficos(self):
        self.fig.clear()

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DATE(data_retirada) as dia, COUNT(*) 
            FROM movimentacoes
            WHERE data_retirada IS NOT NULL
            GROUP BY dia
            ORDER BY dia DESC
            LIMIT 7
        """)
        resultados = cursor.fetchall()
        conn.close()

        if resultados:
            dias_iso = [row[0] for row in reversed(resultados)]
            dias = [formatar_data_br_dia(d) for d in dias_iso]
            qtd = [row[1] for row in reversed(resultados)]
        else:
            dias = []
            qtd = []

        ax = self.fig.add_subplot(111)
        ax.bar(dias, qtd, color='cornflowerblue')
        ax.set_ylabel("Total de Movimentações")
        ax.set_xlabel("Dia")
        ax.set_title("Movimentações (Últimos 7 dias)")
        ax.grid(True, axis='y')

        self.canvas.draw()
