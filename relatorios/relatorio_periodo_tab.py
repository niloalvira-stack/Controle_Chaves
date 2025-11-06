from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QDateEdit, QLabel
)
from PyQt5.QtCore import QDate
import sqlite3
import csv

DB_NAME = "controle_chaves.db"

class RelatorioPorPeriodoTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        filtros_layout = QHBoxLayout()
        filtros_layout.addWidget(QLabel("Data Início:"))
        self.data_inicio = QDateEdit()
        self.data_inicio.setCalendarPopup(True)
        self.data_inicio.setDate(QDate.currentDate())   # Sempre inicia com hoje
        filtros_layout.addWidget(self.data_inicio)

        filtros_layout.addWidget(QLabel("Data Fim:"))
        self.data_fim = QDateEdit()
        self.data_fim.setCalendarPopup(True)
        self.data_fim.setDate(QDate.currentDate())      # Sempre inicia com hoje
        filtros_layout.addWidget(self.data_fim)

        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.clicked.connect(self.load_relatorio)
        filtros_layout.addWidget(btn_filtrar)
        layout.addLayout(filtros_layout)

        self.btn_exportar = QPushButton("Exportar para CSV")
        self.btn_exportar.clicked.connect(self.exportar_csv)
        layout.addWidget(self.btn_exportar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Chave", "Usuário", "Status", "Retirada", "Devolução"]
        )
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.load_relatorio()

    def load_relatorio(self):
        inicio = self.data_inicio.date().toString("yyyy-MM-dd") + " 00:00:00"
        fim = self.data_fim.date().toString("yyyy-MM-dd") + " 23:59:59"
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, chave, usuario, status, data_retirada, data_retorno
                FROM movimentacoes
                WHERE data_retirada >= ? AND data_retirada <= ?
                ORDER BY data_retirada DESC
            """, (inicio, fim))
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
        inicio = self.data_inicio.date().toString("yyyy-MM-dd") + " 00:00:00"
        fim = self.data_fim.date().toString("yyyy-MM-dd") + " 23:59:59"
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, chave, usuario, status, data_retirada, data_retorno
                FROM movimentacoes
                WHERE data_retirada >= ? AND data_retirada <= ?
                ORDER BY data_retirada DESC
            """, (inicio, fim))
            rows = cursor.fetchall()
            conn.close()
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "ID", "Chave", "Usuário", "Status", "Retirada", "Devolução"
                ])
                writer.writerows(rows)
            QMessageBox.information(self, "Sucesso", "Relatório exportado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{e}")
