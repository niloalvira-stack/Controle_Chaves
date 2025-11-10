import os
import csv
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QFormLayout, QLineEdit, QComboBox, QHeaderView,
    QMessageBox, QFileDialog, QDateEdit, QDialogButtonBox, QLabel
)
from PyQt5.QtCore import QDate, QTimer
from PyQt5.QtGui import QBrush, QColor, QIcon
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from utils import montar_display_sala_por_id
from utils.utils_log import log_acao
from .selecionar_sala_dialog import SelecionarSalaDialog  # diálogo modal

DB_NAME = "C:/Controle_Chaves/controle_chaves.db"


def formatar_data_br(data_str):
    if not data_str:
        return ""
    try:
        return datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return data_str


class FiltroMovimentacaoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filtrar Movimentações")
        layout = QFormLayout(self)

        self.data_inicio = QDateEdit(calendarPopup=True)
        self.data_inicio.setDisplayFormat("dd/MM/yyyy")
        self.data_inicio.setDate(QDate.currentDate())

        self.data_fim = QDateEdit(calendarPopup=True)
        self.data_fim.setDisplayFormat("dd/MM/yyyy")
        self.data_fim.setDate(QDate.currentDate())

        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Qualquer usuário (opcional)")

        self.combo_status = QComboBox()
        self.combo_status.addItems(["Todos", "disponível", "indisponível"])

        layout.addRow("Data Início:", self.data_inicio)
        layout.addRow("Data Fim:", self.data_fim)
        layout.addRow("Usuário:", self.input_usuario)
        layout.addRow("Status:", self.combo_status)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_filters(self):
        inicio = self.data_inicio.date().toString("yyyy-MM-dd") + " 00:00:00"
        fim = self.data_fim.date().toString("yyyy-MM-dd") + " 23:59:59"
        usuario = self.input_usuario.text().strip() or None
        status = self.combo_status.currentText()
        if status == "Todos":
            status = None
        return {"data_ini": inicio, "data_fim": fim, "usuario": usuario, "status": status}


def criar_tabela_movimentacoes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT NOT NULL,
            usuario TEXT NOT NULL,
            data_retirada TIMESTAMP,
            data_retorno TIMESTAMP,
            status TEXT DEFAULT 'disponível'
        )
    """)
    conn.commit()
    conn.close()


def listar_movimentacoes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, chave, usuario, data_retirada, data_retorno, status
        FROM movimentacoes
        ORDER BY data_retirada DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def buscar_movimentacoes_personalizado(chave=None, usuario=None, data_ini=None, data_fim=None, status=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = """
        SELECT id, chave, usuario, data_retirada, data_retorno, status 
        FROM movimentacoes WHERE 1=1
    """
    params = []
    if chave:
        query += " AND chave LIKE ?"
        params.append(f"%{chave}%")
    if usuario:
        query += " AND usuario LIKE ?"
        params.append(f"%{usuario}%")
    if data_ini:
        query += " AND (data_retirada >= ?)"
        params.append(data_ini)
    if data_fim:
        query += " AND (data_retirada <= ?)"
        params.append(data_fim)
    if status and status.lower() not in ["todos", ""]:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY data_retirada DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def registrar_retirada(sala_id, chave_display, usuario):
    """
    Registra movimentação de retirada e marca a sala como indisponível.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    data_retirada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO movimentacoes (chave, usuario, data_retirada, status) VALUES (?, ?, ?, ?)",
        (chave_display, usuario, data_retirada, "indisponível")
    )

    cursor.execute(
        "UPDATE salas SET status = 'indisponivel' WHERE id = ?",
        (sala_id,)
    )

    conn.commit()
    conn.close()


def registrar_devolucao(mov_id, chave, sala_id):
    """
    Registra devolução na movimentação e marca a sala como disponível.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    data_retorno = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "UPDATE movimentacoes SET data_retorno=?, status='disponível' WHERE id=? AND chave=?",
        (data_retorno, mov_id, chave)
    )

    cursor.execute(
        "UPDATE salas SET status = 'disponivel' WHERE id = ?",
        (sala_id,)
    )

    conn.commit()
    conn.close()


class MovimentacoesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.sala_id_atual = None  # id da sala escolhida no diálogo
        self.init_ui()
        criar_tabela_movimentacoes()
        self.carregar_movimentacoes()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.carregar_movimentacoes)
        self.timer.start(5000)

    def init_ui(self):
        layout = QVBoxLayout(self)
        label = QLabel("Movimentações de Chaves/Salas")
        layout.addWidget(label)

        form_layout = QHBoxLayout()

        # Campo de sala selecionada + botão para abrir o diálogo
        self.label_sala_selecionada = QLineEdit()
        self.label_sala_selecionada.setReadOnly(True)

        self.btn_escolher_sala = QPushButton("Selecionar sala...")
        self.btn_escolher_sala.setObjectName("btnEscolherSala")
        self.btn_escolher_sala.clicked.connect(self.abrir_dialogo_salas)

        form_layout.addWidget(QLabel("Sala:"))
        form_layout.addWidget(self.label_sala_selecionada)
        form_layout.addWidget(self.btn_escolher_sala)

        # Usuário
        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Usuário")
        form_layout.addWidget(self.input_usuario)

        # Botões de ação
        self.btn_retirar = QPushButton("Registrar Retirada")
        self.btn_retirar.setObjectName("btnRetirar")
        self.btn_retirar.clicked.connect(self.adicionar_movimentacao)

        self.btn_devolver = QPushButton("Registrar Devolução")
        self.btn_devolver.setObjectName("btnDevolver")
        self.btn_devolver.clicked.connect(self.devolver_selecionada)

        form_layout.addWidget(self.btn_retirar)
        form_layout.addWidget(self.btn_devolver)
        layout.addLayout(form_layout)

        # Botão de filtro
        filter_btn_box = QHBoxLayout()
        self.btn_filtrar = QPushButton("Filtrar Movimentações")
        self.btn_filtrar.setObjectName("btnFiltrar")
        self.btn_filtrar.clicked.connect(self.abrir_filtro_modal)
        filter_btn_box.addWidget(self.btn_filtrar)
        layout.addLayout(filter_btn_box)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Chave", "Usuário", "Retirada", "Devolução", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setColumnHidden(0, True)
        layout.addWidget(self.table)

        self.setLayout(layout)

        # Estilo visual dos botões
        self.setStyleSheet("""
            QPushButton {
                padding: 10px 24px;          /* altura e largura maiores */
                min-height: 34px;            /* altura mínima do botão */
                min-width: 140px;            /* largura mínima */
                border-radius: 6px;
                border: 1px solid #888;
                font-weight: 500;
            }
            QPushButton#btnEscolherSala {
                background-color: #eeeeee;
            }
            QPushButton#btnEscolherSala:hover {
                background-color: #f5f5f5;
            }

            QPushButton#btnRetirar {
                background-color: #2e7d32;
                color: white;
                border: 1px solid #1b5e20;
            }
            QPushButton#btnRetirar:hover {
                background-color: #388e3c;
            }
            QPushButton#btnRetirar:pressed {
                background-color: #1b5e20;
            }

            QPushButton#btnDevolver {
                background-color: #1565c0;
                color: white;
                border: 1px solid #0d47a1;
            }
            QPushButton#btnDevolver:hover {
                background-color: #1976d2;
            }
            QPushButton#btnDevolver:pressed {
                background-color: #0d47a1;
            }

            QPushButton#btnFiltrar {
                background-color: #f9a825;
                color: #333333;
                border: 1px solid #f57f17;
            }
            QPushButton#btnFiltrar:hover {
                background-color: #fbc02d;
            }
            QPushButton#btnFiltrar:pressed {
                background-color: #f57f17;
            }
        """)

    def abrir_dialogo_salas(self):
        dlg = SelecionarSalaDialog(self)
        if dlg.exec():
            self.sala_id_atual = dlg.sala_id_selecionada
            self.label_sala_selecionada.setText(dlg.sala_display_selecionada)

    def abrir_filtro_modal(self):
        dialog = FiltroMovimentacaoDialog(self)
        if dialog.exec():
            filtros = dialog.get_filters()
            resultados = buscar_movimentacoes_personalizado(
                None, filtros["usuario"], filtros["data_ini"], filtros["data_fim"], filtros["status"]
            )
            self.exibir_historico(resultados)

    def carregar_movimentacoes(self):
        self.exibir_historico(listar_movimentacoes())

    def exibir_historico(self, historico):
        self.table.setRowCount(0)
        now = datetime.now()
        for row_data in historico:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            for col_idx, value in enumerate(row_data):
                if col_idx in [3, 4]:
                    value = formatar_data_br(value)
                item = QTableWidgetItem(str(value if value else ""))
                if col_idx == 5:
                    status = row_data[5]
                    icone = ""
                    if status == "disponível":
                        item.setBackground(QBrush(QColor(144, 238, 144)))
                        icone = "check.png"
                    elif status == "indisponível":
                        retirada_str = row_data[3]
                        try:
                            if retirada_str:
                                retirada_dt = datetime.strptime(retirada_str, "%Y-%m-%d %H:%M:%S")
                                diff_horas = (now - retirada_dt).total_seconds() / 3600
                                if diff_horas > 24:
                                    item.setBackground(QBrush(QColor(255, 215, 0)))
                                    icone = "alert.png"
                                else:
                                    item.setBackground(QBrush(QColor(255, 120, 120)))
                                    icone = "warning.png"
                            else:
                                item.setBackground(QBrush(QColor(255, 120, 120)))
                                icone = "warning.png"
                        except Exception:
                            item.setBackground(QBrush(QColor(255, 120, 120)))
                            icone = "warning.png"
                    if icone and os.path.exists(f"icons/{icone}"):
                        item.setIcon(QIcon(f"icons/{icone}"))
                self.table.setItem(row_idx, col_idx, item)

    def adicionar_movimentacao(self):
        sala_id = self.sala_id_atual
        usuario = self.input_usuario.text().strip()

        if not sala_id:
            QMessageBox.warning(self, "Erro", "Selecione uma sala para registrar a retirada.")
            log_acao(f"Tentativa de retirada inválida: sala_id={sala_id}, usuario='{usuario}'")
            return
        if not usuario:
            QMessageBox.warning(self, "Erro", "Preencha o usuário.")
            log_acao(f"Tentativa de retirada com usuário vazio: sala_id={sala_id}")
            return

        chave_registro = montar_display_sala_por_id(sala_id)

        try:
            registrar_retirada(sala_id, chave_registro, usuario)
            log_acao(f"Retirada registrada: chave='{chave_registro}', usuario='{usuario}'")
            QMessageBox.information(
                self,
                "Sucesso",
                f"Retirada registrada para a chave '{chave_registro}'!"
            )
            self.sala_id_atual = None
            self.label_sala_selecionada.clear()
            self.input_usuario.clear()
            self.carregar_movimentacoes()
        except Exception as e:
            log_acao(f"Erro ao registrar retirada: chave='{chave_registro}', usuario='{usuario}', erro={e}")
            QMessageBox.critical(self, "Erro", f"Falha ao registrar retirada:\n{e}")

    def _obter_sala_id_por_display(self, display):
        """
        Localiza o id da sala a partir do texto de display (mesmo padrão do montar_display_sala_por_id).
        """
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM salas")
        rows = cursor.fetchall()
        conn.close()

        for (sid,) in rows:
            if montar_display_sala_por_id(sid) == display:
                return sid
        return None

    def devolver_selecionada(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Atenção", "Selecione uma movimentação para registrar devolução!")
            log_acao("Tentativa de devolução sem seleção na tabela")
            return

        row = selected[0].row()
        mov_id = int(self.table.item(row, 0).text())
        chave_nome = self.table.item(row, 1).text()
        status = self.table.item(row, 5).text()

        if status == "disponível":
            QMessageBox.information(self, "Info", "Esta movimentação já está devolvida!")
            log_acao(f"Tentativa de devolução já devolvida: mov_id={mov_id}, chave='{chave_nome}'")
            return

        sala_id = self._obter_sala_id_por_display(chave_nome)
        if sala_id is None:
            QMessageBox.critical(self, "Erro", "Não foi possível localizar a sala desta movimentação.")
            log_acao(f"Erro ao localizar sala para devolução: mov_id={mov_id}, chave='{chave_nome}'")
            return

        try:
            registrar_devolucao(mov_id, chave_nome, sala_id)
            log_acao(f"Devolução registrada: mov_id={mov_id}, chave='{chave_nome}'")
            QMessageBox.information(self, "Sucesso", "Devolução registrada!")
            self.carregar_movimentacoes()
        except Exception as e:
            log_acao(f"Erro ao registrar devolução: mov_id={mov_id}, chave='{chave_nome}', erro={e}")
            QMessageBox.critical(self, "Erro", f"Falha ao registrar devolução:\n{e}")

    def obter_dados_da_tabela(self):
        dados = []
        row_count = self.table.rowCount()
        col_count = self.table.columnCount()
        for row in range(row_count):
            linha = []
            for col in range(col_count):
                item = self.table.item(row, col)
                linha.append(item.text() if item else "")
            dados.append(linha)
        return dados

    def exportar_csv(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar como CSV", "", "CSV Files (*.csv)")
        if caminho:
            dados = self.obter_dados_da_tabela()
            with open(caminho, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Chave", "Usuário", "Retirada", "Devolução", "Status"])
                for row in dados:
                    row = list(row)
                    row[3] = formatar_data_br(row[3])
                    row[4] = formatar_data_br(row[4])
                    writer.writerow(row)
            QMessageBox.information(self, "Exportação", "Movimentações exportadas para CSV com sucesso!")

    def exportar_pdf(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar como PDF", "", "PDF Files (*.pdf)")
        if caminho:
            dados = self.obter_dados_da_tabela()
            c = canvas.Canvas(caminho, pagesize=A4)
            width, height = A4
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "Relatório de Movimentações")
            c.setFont("Helvetica", 12)
            cabecalho = ["ID", "Chave", "Usuário", "Retirada", "Devolução", "Status"]
            y = height - 80
            c.drawString(50, y, " | ".join(cabecalho))
            y -= 20
            for row in dados:
                row = list(row)
                row[3] = formatar_data_br(row[3])
                row[4] = formatar_data_br(row[4])
                c.drawString(50, y, " | ".join([str(x) if x else "" for x in row]))
                y -= 20
                if y < 50:
                    c.showPage()
                    y = height - 50
            c.save()
            QMessageBox.information(self, "Exportação", "Movimentações exportadas para PDF com sucesso!")
