from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QPushButton,
    QFileDialog, QMessageBox, QHBoxLayout
)
import os
import shutil

from datetime import datetime

from admin.usuarios import UsuariosTab
from admin.predios import PrediosTab
from admin.anexos import AnexosTab
from admin.salas import SalasTab

from database_module import DB_NAME  # se você expor o caminho lá
from utils.utils_log import log_acao, LOG_PATH


class AdminTab(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        self.tabs.addTab(UsuariosTab(), "Usuários")
        self.tabs.addTab(SalasTab(), "Salas")
        self.tabs.addTab(PrediosTab(), "Prédios")
        self.tabs.addTab(AnexosTab(), "Anexos")

        # linha de botões (backup / restore)
        btns_layout = QHBoxLayout()

        self.btn_backup = QPushButton("Backup do Banco de Dados")
        self.btn_backup.setObjectName("btnBackupDb")
        self.btn_backup.clicked.connect(self.fazer_backup)
        btns_layout.addWidget(self.btn_backup)

        self.btn_restore = QPushButton("Restaurar Banco de Dados")
        self.btn_restore.setObjectName("btnRestoreDb")
        self.btn_restore.clicked.connect(self.fazer_restore)
        btns_layout.addWidget(self.btn_restore)

        self.layout.addLayout(btns_layout)

        self.setStyleSheet("""
            QPushButton {
                padding: 10px 24px;
                min-height: 34px;
                min-width: 160px;
                border-radius: 6px;
                border: 1px solid #888;
                font-weight: 500;
            }
            QPushButton#btnBackupDb {
                background-color: #2e7d32;
                color: white;
                border: 1px solid #1b5e20;
            }
            QPushButton#btnBackupDb:hover {
                background-color: #388e3c;
            }
            QPushButton#btnBackupDb:pressed {
                background-color: #1b5e20;
            }
            QPushButton#btnRestoreDb {
                background-color: #c62828;
                color: white;
                border: 1px solid #8e0000;
            }
            QPushButton#btnRestoreDb:hover {
                background-color: #d32f2f;
            }
            QPushButton#btnRestoreDb:pressed {
                background-color: #8e0000;
            }
        """)

    # === helper para acessar o DashMain e usar o feed ===
    def _get_dash_main(self):
        janela = self.parentWidget()
        while janela is not None and janela.__class__.__name__ != "DashMain":
            janela = janela.parentWidget()
        return janela

    def fazer_backup(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar backup do banco", "", "Arquivo SQLite (*.db)"
        )
        if not caminho:
            return

        try:
            shutil.copyfile(DB_NAME, caminho)
            log_acao(f"Backup realizado: {caminho}")

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Backup do banco concluído com sucesso.")

            # Se ainda quiser, pode manter um aviso simples:
            # QMessageBox.information(self, "Backup", "Backup realizado com sucesso!")

        except Exception as e:
            log_acao(f"Erro ao realizar backup: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao realizar backup: {e}")

    def fazer_restore(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Restaurar banco de backup", "", "Arquivo SQLite (*.db)"
        )
        if not caminho:
            return

        reply = QMessageBox.question(
            self,
            "Confirmação",
            "Atenção! Restaurar o backup irá substituir seu banco atual "
            "e pode causar perda de dados recentes.\nTem certeza?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            shutil.copyfile(caminho, DB_NAME)
            log_acao(f"Restore realizado: {caminho} -> {DB_NAME}")

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Banco restaurado com sucesso.")

            # Opcional manter:
            # QMessageBox.information(self, "Restaurar", "Banco restaurado com sucesso!")

        except Exception as e:
            log_acao(f"Erro ao restaurar banco: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao restaurar banco: {e}")
