from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, QComboBox, QLabel
import sqlite3
import csv

DB_NAME = "controle_chaves.db"

class RelatorioPorSalaTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Chave:"))
        self.cb_chave = QComboBox()
        filtro_layout.addWidget(self.cb_chave)
        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.clicked.connect(self.load_relatorio)
        filtro_layout.addWidget(btn_filtrar)
        layout.addLayout(filtro_layout)

        self.btn_exportar = QPushButton("Exportar para CSV")
        self.btn_exportar.clicked.connect(self.exportar_csv)
        layout.addWidget(self.btn_exportar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Chave", "Usuário", "Status", "Retirada", "Devolução"])
        layout.addWidget(self.table)

        self.load_chaves()
        self.load_relatorio()

    def load_chaves(self):
        self.cb_chave.clear()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT DISTINCT chave FROM movimentacoes ORDER BY chave")
        chaves = [row[0] for row in c.fetchall()]
        self.cb_chave.addItems(chaves or [""])
        conn.close()

    def load_relatorio(self):
        chave = self.cb_chave.currentText()
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, chave, usuario, status, data_retirada, data_retorno
                FROM movimentacoes
                WHERE chave = ?
                ORDER BY data_retirada DESC
            """, (chave,))
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    self.table.setItem(i, j, QTableWidgetItem(str(val) if val else ""))
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar relatório:\n{e}")

    def exportar_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        chave = self.cb_chave.currentText()
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, chave, usuario, status, data_retirada, data_retorno
                FROM movimentacoes
                WHERE chave = ?
                ORDER BY data_retirada DESC
            """, (chave,))
            rows = cursor.fetchall()
            conn.close()
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Chave", "Usuário", "Status", "Retirada", "Devolução"])
                writer.writerows(rows)
            QMessageBox.information(self, "Sucesso", "Relatório exportado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{e}")
