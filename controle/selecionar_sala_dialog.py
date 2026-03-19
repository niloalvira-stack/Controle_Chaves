# controle/selecionar_sala_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QHeaderView, QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor

from database_module import get_connection  # usa o mesmo módulo oficial


class SelecionarSalaDialog(QDialog):
    """
    Diálogo modal para listar TODAS as salas e permitir selecionar uma.
    Mostra nome, prédio, anexo e status diretamente do banco.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Sala")

        self.setFixedSize(800, 500)

        self.sala_id_selecionada = None
        self.sala_display_selecionada = None

        layout = QVBoxLayout(self)

        # Filtro de texto
        filtro_layout = QHBoxLayout()
        self.input_filtro = QLineEdit()
        self.input_filtro.setPlaceholderText("Filtrar por sala / prédio / anexo")
        self.input_filtro.textChanged.connect(self.aplicar_filtro)
        filtro_layout.addWidget(QLabel("Filtro:"))
        filtro_layout.addWidget(self.input_filtro)
        layout.addLayout(filtro_layout)

        # Tabela de salas
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Sala", "Prédio", "Anexo", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.cellDoubleClicked.connect(self.selecionar_e_fechar)
        layout.addWidget(self.table)

        # Botões OK / Cancelar
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.on_ok)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self.setLayout(layout)

        # Carregar dados
        self._carregar_salas()
        self._todas_linhas = self._capturar_linhas()  # cache para filtro

        # Centralizar em relação ao pai (se houver)
        if parent is not None:
            geo = parent.frameGeometry()
            center = geo.center()
            self.move(center - self.rect().center())

    def _carregar_salas(self):
        self.table.setRowCount(0)

        try:
            conn = get_connection()
            if conn is None:
                QMessageBox.critical(self, "Erro", "Falha ao conectar ao banco de dados.")
                return

            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.id,
                       s.nome,
                       p.nome AS predio_nome,
                       a.nome AS anexo_nome,
                       s.status
                FROM salas s
                LEFT JOIN predios p ON s.predio_id = p.id
                LEFT JOIN anexos a ON s.anexo_id = a.id
                ORDER BY s.nome
                """
            )
            rows = cursor.fetchall()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar salas:\n{e}")
            return

        # rows: lista de tuplas (id, nome, predio_nome, anexo_nome, status)
        for row in rows:
            sid, nome, predio, anexo, status = row

            # converte bytes -> str
            if isinstance(nome, (bytes, bytearray)):
                nome = nome.decode("utf-8", errors="ignore")
            if isinstance(predio, (bytes, bytearray)):
                predio = predio.decode("utf-8", errors="ignore")
            if isinstance(anexo, (bytes, bytearray)):
                anexo = anexo.decode("utf-8", errors="ignore")
            if isinstance(status, (bytes, bytearray)):
                status = status.decode("utf-8", errors="ignore")

            status = status or ""

            r = self.table.rowCount()
            self.table.insertRow(r)

            item_sala = QTableWidgetItem(nome or "")
            item_sala.setData(Qt.UserRole, sid)
            self.table.setItem(r, 0, item_sala)

            self.table.setItem(r, 1, QTableWidgetItem(predio or ""))
            self.table.setItem(r, 2, QTableWidgetItem(anexo or ""))

            item_status = QTableWidgetItem(status)

            if status == "disponivel":
                # verde
                item_status.setBackground(QBrush(QColor(144, 238, 144)))
            elif status == "indisponivel":
                # amarelo
                item_status.setBackground(QBrush(QColor(255, 215, 0)))
            elif status == "atrasado":
                # vermelho
                item_status.setBackground(QBrush(QColor(255, 120, 120)))

            self.table.setItem(r, 3, item_status)

    def _capturar_linhas(self):
        """
        Guarda snapshot de todas as linhas (para aplicar filtro em memória).
        """
        dados = []
        for row in range(self.table.rowCount()):
            sala_item = self.table.item(row, 0)
            predio_item = self.table.item(row, 1)
            anexo_item = self.table.item(row, 2)
            status_item = self.table.item(row, 3)

            if not sala_item:
                continue

            sala = sala_item.text()
            predio = predio_item.text() if predio_item else ""
            anexo = anexo_item.text() if anexo_item else ""
            status = status_item.text() if status_item else ""
            sid = sala_item.data(Qt.UserRole)
            dados.append((sala, predio, anexo, status, sid))
        return dados

    def aplicar_filtro(self, texto):
        texto = texto.strip().lower()
        self.table.setRowCount(0)
        for sala, predio, anexo, status, sid in self._todas_linhas:
            if (not texto or
                texto in sala.lower() or
                texto in (predio or "").lower() or
                texto in (anexo or "").lower()):
                r = self.table.rowCount()
                self.table.insertRow(r)

                item_sala = QTableWidgetItem(sala)
                item_sala.setData(Qt.UserRole, sid)
                self.table.setItem(r, 0, item_sala)

                self.table.setItem(r, 1, QTableWidgetItem(predio or ""))
                self.table.setItem(r, 2, QTableWidgetItem(anexo or ""))

                item_status = QTableWidgetItem(status or "")

                if status == "disponivel":
                    item_status.setBackground(QBrush(QColor(144, 238, 144)))
                elif status == "indisponivel":
                    item_status.setBackground(QBrush(QColor(255, 215, 0)))
                elif status == "atrasado":
                    item_status.setBackground(QBrush(QColor(255, 120, 120)))

                self.table.setItem(r, 3, item_status)

    def _pegar_selecao(self):
        selected = self.table.selectedItems()
        if not selected:
            return None, None
        row = selected[0].row()
        item_sala = self.table.item(row, 0)
        sid = item_sala.data(Qt.UserRole)
        display = item_sala.text()
        return sid, display

    def on_ok(self):
        sid, display = self._pegar_selecao()
        if sid is None:
            QMessageBox.warning(self, "Atenção", "Selecione uma sala.")
            return
        self.sala_id_selecionada = sid
        self.sala_display_selecionada = display
        self.accept()

    def selecionar_e_fechar(self, row, col):
        item_sala = self.table.item(row, 0)
        sid = item_sala.data(Qt.UserRole)
        display = item_sala.text()
        self.sala_id_selecionada = sid
        self.sala_display_selecionada = display
        self.accept()
