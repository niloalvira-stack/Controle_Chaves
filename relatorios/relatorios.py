from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QFileDialog
from database import get_connection
import csv

class RelatoriosTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.btn_exportar = QPushButton("Exportar Movimentações")
        self.btn_exportar.clicked.connect(self.exportar_csv)
        layout.addWidget(self.btn_exportar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Sala", "Usuário", "Status", "Data"])
        layout.addWidget(self.table)

        self.load_relatorio()

    def load_relatorio(self):
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT ch.id, s.nome, ch.usuario, ch.status, ch.data
            FROM chaves ch
            JOIN salas s ON ch.sala_id = s.id
            ORDER BY ch.id
        """)
        rows = c.fetchall()
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        conn.close()

    def exportar_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT ch.id, s.nome, ch.usuario, ch.status, ch.data
            FROM chaves ch
            JOIN salas s ON ch.sala_id = s.id
            ORDER BY ch.id
        """)
        rows = c.fetchall()
        conn.close()
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Sala", "Usuário", "Status", "Data"])
            writer.writerows(rows)
