# controle/movimentacoes.py
import os
import csv
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QFormLayout, QLineEdit, QComboBox, QHeaderView,
    QMessageBox, QFileDialog, QDateEdit, QDialogButtonBox, QLabel, QToolButton
)
from PyQt5.QtCore import QDate, QTimer
from PyQt5.QtGui import QBrush, QColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from utils.validacao import email_valido
from utils.utils import montar_display_sala_por_id
from utils.utils_log import log_acao
from .selecionar_sala_dialog import SelecionarSalaDialog
from autenticacao.helpers_autenticacao import get_current_user

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DB_NAME = os.path.join(BASE_DIR, "controle_chaves.db")
ALERTA_HORAS = 4


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
        self.input_usuario.setPlaceholderText("Qualquer utilizador (opcional)")

        self.combo_status = QComboBox()
        self.combo_status.addItems(["Todos", "disponível", "indisponível"])

        layout.addRow("Data Início:", self.data_inicio)
        layout.addRow("Data Fim:", self.data_fim)
        layout.addRow("Utilizador:", self.input_usuario)
        layout.addRow("Status:", self.combo_status)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_filters(self):
        inicio = self.data_inicio.date().toString("yyyy-MM-dd") + " 00:00:00"
        fim = self.data_fim.date().toString("yyyy-MM-dd") + " 23:59:59"
        usuario = self.input_usuario.text().strip().lower() or None
        status = self.combo_status.currentText()
        if status == "Todos":
            status = None
        return {"data_ini": inicio, "data_fim": fim, "usuario": usuario, "status": status}


def criar_tabela_utilizadores():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS utilizadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome  TEXT NOT NULL,
            email TEXT,
            ativo INTEGER NOT NULL DEFAULT 1
        )
    """)
    cur.execute("PRAGMA table_info(utilizadores)")
    cols = [r[1] for r in cur.fetchall()]
    if "ativo" not in cols:
        cur.execute("ALTER TABLE utilizadores ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1")
    conn.commit()
    conn.close()


def criar_tabela_movimentacoes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT NOT NULL,
            usuario TEXT,
            email TEXT,
            data_retirada TIMESTAMP,
            data_retorno TIMESTAMP,
            status TEXT DEFAULT 'disponível',
            alerta_enviado INTEGER DEFAULT 0
        )
    """)
    cursor.execute("PRAGMA table_info(movimentacoes)")
    cols = [r[1] for r in cursor.fetchall()]
    if "utilizador_id" not in cols:
        cursor.execute("ALTER TABLE movimentacoes ADD COLUMN utilizador_id INTEGER")
    conn.commit()
    conn.close()


def listar_movimentacoes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id,
               m.chave,
               COALESCE(u.nome, m.usuario) AS utilizador,
               COALESCE(m.email, u.email) AS email,
               m.data_retirada,
               m.data_retorno,
               m.status
        FROM movimentacoes m
        LEFT JOIN utilizadores u ON u.id = m.utilizador_id
        ORDER BY m.data_retirada DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def buscar_movimentacoes_personalizado(chave=None, usuario=None, data_ini=None, data_fim=None, status=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = """
        SELECT m.id,
               m.chave,
               COALESCE(u.nome, m.usuario) AS utilizador,
               COALESCE(m.email, u.email) AS email,
               m.data_retirada,
               m.data_retorno,
               m.status
        FROM movimentacoes m
        LEFT JOIN utilizadores u ON u.id = m.utilizador_id
        WHERE 1=1
    """
    params = []
    if chave:
        query += " AND m.chave LIKE ?"
        params.append(f"%{chave}%")
    if usuario:
        usuario = usuario.strip().lower()
        query += " AND LOWER(COALESCE(u.nome, m.usuario)) LIKE ?"
        params.append(f"%{usuario}%")
    if data_ini:
        query += " AND (m.data_retirada >= ?)"
        params.append(data_ini)
    if data_fim:
        query += " AND (m.data_retirada <= ?)"
        params.append(data_fim)
    if status and status.lower() not in ["todos", ""]:
        query += " AND m.status = ?"
        params.append(status)
    query += " ORDER BY m.data_retirada DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def registrar_retirada(sala_id, chave_display, utilizador_id, email):
    email = (email or "").strip().lower()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    data_retirada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "SELECT nome, ativo FROM utilizadores WHERE id = ?",
        (utilizador_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Utilizador id={utilizador_id} não encontrado na tabela utilizadores")
    nome_utilizador, ativo = row
    if not ativo:
        conn.close()
        raise ValueError(f"Utilizador id={utilizador_id} está desativado e não pode retirar chaves")

    if not nome_utilizador:
        conn.close()
        raise ValueError(f"Utilizador id={utilizador_id} não possui nome válido")

    cursor.execute(
        """
        INSERT INTO movimentacoes (
            chave, utilizador_id, usuario, email, data_retirada, status, alerta_enviado
        )
        VALUES (?, ?, ?, ?, ?, ?, 0)
        """,
        (chave_display, utilizador_id, nome_utilizador, email, data_retirada, "indisponível")
    )

    cursor.execute(
        "UPDATE salas SET status = 'indisponivel' WHERE id = ?",
        (sala_id,)
    )

    conn.commit()
    conn.close()


def registrar_devolucao(mov_id, chave, sala_id):
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
        self.sala_id_atual = None
        print("MovimentacoesTab.__init__ entrou")

        self.init_ui()
        print("UI criada")

        try:
            criar_tabela_utilizadores()
            criar_tabela_movimentacoes()
            print("Tabelas criadas")
            self.carregar_movimentacoes()
            print("Movimentações carregadas")
        except Exception as e:
            user = get_current_user()
            user_login = user["login"] if user else "sistema"
            log_acao(
                action="init_movimentacoes",
                user=user_login,
                status="error",
                details=f"Erro ao inicializar tabela/carregar movimentações: {e}",
            )
            QMessageBox.critical(self, "Erro", f"Falha ao carregar movimentações:\n{e}")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.carregar_movimentacoes)
        self.timer.start(5000)

    def _get_dash_main(self):
        from interface.dash_main import DashMain  # import local, evita ciclo
        janela = self.parentWidget()
        while janela is not None and not isinstance(janela, DashMain):
            janela = janela.parentWidget()
        return janela

    def acao_verificar_pendencias(self):
        qtd = verificar_pendencias_e_enviar_emails()
        if qtd > 0:
            QMessageBox.information(
                self,
                "Pendências",
                f"Foram encontradas {qtd} pendência(s) em atraso (registradas no log)."
            )
        else:
            QMessageBox.information(
                self,
                "Pendências",
                "Nenhuma pendência em atraso encontrada."
            )

    def init_ui(self):
        layout = QVBoxLayout(self)
        label = QLabel("Movimentações de Chaves/Salas")
        layout.addWidget(label)

        form_layout = QHBoxLayout()

        self.label_sala_selecionada = QLineEdit()
        self.label_sala_selecionada.setReadOnly(True)

        self.btn_escolher_sala = QPushButton("Selecionar sala...")
        self.btn_escolher_sala.setObjectName("btnEscolherSala")
        self.btn_escolher_sala.clicked.connect(self.abrir_dialogo_salas)

        form_layout.addWidget(QLabel("Sala:"))
        form_layout.addWidget(self.label_sala_selecionada)
        form_layout.addWidget(self.btn_escolher_sala)

        self.combo_utilizador = QComboBox()
        self.combo_utilizador.setEditable(False)

        self.btn_novo_utilizador = QToolButton()
        self.btn_novo_utilizador.setText("+")
        self.btn_novo_utilizador.setToolTip("Cadastrar novo utilizador")
        self.btn_novo_utilizador.clicked.connect(self.cadastrar_utilizador_rapido)

        form_layout.addWidget(self.combo_utilizador)
        form_layout.addWidget(self.btn_novo_utilizador)

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("E-mail")
        form_layout.addWidget(self.input_email)

        self.btn_retirar = QPushButton("Registrar Retirada")
        self.btn_retirar.setObjectName("btnRetirar")
        self.btn_retirar.clicked.connect(self.adicionar_movimentacao)

        self.btn_devolver = QPushButton("Registrar Devolução")
        self.btn_devolver.setObjectName("btnDevolver")
        self.btn_devolver.clicked.connect(self.devolver_selecionada)

        form_layout.addWidget(self.btn_retirar)
        form_layout.addWidget(self.btn_devolver)
        layout.addLayout(form_layout)

        filter_btn_box = QHBoxLayout()
        self.btn_filtrar = QPushButton("Filtrar Movimentações")
        self.btn_filtrar.setObjectName("btnFiltrar")
        self.btn_filtrar.clicked.connect(self.abrir_filtro_modal)
        filter_btn_box.addWidget(self.btn_filtrar)

        self.btn_verificar_pendencias = QPushButton("Verificar pendências")
        self.btn_verificar_pendencias.setObjectName("btnVerificarPendencias")
        self.btn_verificar_pendencias.clicked.connect(self.acao_verificar_pendencias)
        filter_btn_box.addWidget(self.btn_verificar_pendencias)

        layout.addLayout(filter_btn_box)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Chave", "Utilizador", "E-mail", "Retirada", "Devolução", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setColumnHidden(0, True)
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.setStyleSheet("""
            QPushButton {
                padding: 10px 24px;
                min-height: 34px;
                min-width: 140px;
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

            QPushButton#btnFiltrar, QPushButton#btnVerificarPendencias {
                background-color: #f9a825;
                color: #333333;
                border: 1px solid #f57f17;
            }
            QPushButton#btnFiltrar:hover, QPushButton#btnVerificarPendencias:hover {
                background-color: #fbc02d;
            }
            QPushButton#btnFiltrar:pressed, QPushButton#btnVerificarPendencias:pressed {
                background-color: #f57f17;
            }
        """)

        self.load_utilizadores_combo()

    def load_utilizadores_combo(self):
        self.combo_utilizador.clear()
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nome, email
            FROM utilizadores
            WHERE ativo = 1
            ORDER BY nome
        """)
        rows = cur.fetchall()
        conn.close()

        self.combo_utilizador.addItem("Selecione o utilizador...", None)
        for uid, nome, email in rows:
            display = f"{nome} ({email})" if email else nome
            self.combo_utilizador.addItem(display, uid)

    def cadastrar_utilizador_rapido(self):
        from admin.utilizadores_tab import UtilizadorDialog

        dialog = UtilizadorDialog(self)
        if dialog.exec():
            dados = dialog.get_dados()
            nome = dados["nome"]
            email = dados["email"]

            if not nome:
                QMessageBox.warning(self, "Erro", "Nome do utilizador é obrigatório.")
                return

            try:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO utilizadores (nome, email, ativo) VALUES (?, ?, 1)",
                    (nome, email),
                )
                novo_id = cur.lastrowid
                conn.commit()
                conn.close()

                self.load_utilizadores_combo()
                for idx in range(self.combo_utilizador.count()):
                    if self.combo_utilizador.itemData(idx) == novo_id:
                        self.combo_utilizador.setCurrentIndex(idx)
                        break

                QMessageBox.information(self, "Utilizador", "Utilizador cadastrado com sucesso!")
                dash = self._get_dash_main()
                if dash is not None:
                    dash.show_operation_done("Utilizador cadastrado")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cadastrar utilizador:\n{e}")

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
        historico = listar_movimentacoes()
        self.exibir_historico(historico)

    def exibir_historico(self, historico):
        self.table.setRowCount(0)
        now = datetime.now()

        for row_idx, row_data in enumerate(historico):
            self.table.insertRow(row_idx)

            for col_idx, value in enumerate(row_data):
                if col_idx in [4, 5]:
                    value = formatar_data_br(value)

                item = QTableWidgetItem(str(value if value else ""))

                if col_idx == 6:
                    status = row_data[6] or ""
                    if status == "disponível":
                        item.setBackground(QBrush(QColor(144, 238, 144)))
                    elif status == "indisponível":
                        retirada_str = row_data[4]
                        try:
                            if retirada_str:
                                retirada_dt = datetime.strptime(retirada_str, "%Y-%m-%d %H:%M:%S")
                                diff_horas = (now - retirada_dt).total_seconds() / 3600
                                if diff_horas >= ALERTA_HORAS:
                                    item.setBackground(QBrush(QColor(255, 120, 120)))
                                else:
                                    item.setBackground(QBrush(QColor(255, 215, 0)))
                            else:
                                item.setBackground(QBrush(QColor(255, 215, 0)))
                        except Exception:
                            item.setBackground(QBrush(QColor(255, 215, 0)))

                self.table.setItem(row_idx, col_idx, item)

    def adicionar_movimentacao(self):
        sala_id = self.sala_id_atual
        utilizador_id = self.combo_utilizador.currentData()
        email = self.input_email.text().strip().lower()

        user = get_current_user()
        user_login = user["login"] if user else "desconhecido"

        if not sala_id:
            QMessageBox.warning(self, "Erro", "Selecione uma sala para registrar a retirada.")
            log_acao(
                action="retirada",
                user=user_login,
                resource=f"sala_id={sala_id}",
                status="error",
                details=f"Sem sala selecionada; utilizador_id={utilizador_id}, email='{email}'",
            )
            return

        if utilizador_id is None:
            QMessageBox.warning(self, "Erro", "Selecione o utilizador.")
            log_acao(
                action="retirada",
                user=user_login,
                resource=f"sala_id={sala_id}",
                status="error",
                details=f"Utilizador não selecionado; email='{email}'",
            )
            return

        if email and not email_valido(email):
            QMessageBox.warning(self, "Erro", "Informe um e-mail válido.")
            log_acao(
                action="retirada",
                user=user_login,
                resource=f"sala_id={sala_id}",
                status="error",
                details=f"E-mail inválido; utilizador_id={utilizador_id}, email='{email}'",
            )
            return

        chave_registro = montar_display_sala_por_id(sala_id)

        try:
            registrar_retirada(sala_id, chave_registro, utilizador_id, email)
            log_acao(
                action="retirada",
                user=user_login,
                resource=chave_registro,
                status="success",
                details=f"utilizador_id={utilizador_id}, email='{email}'",
            )

            # limpa UI e recarrega tabela
            self.sala_id_atual = None
            self.label_sala_selecionada.clear()
            self.combo_utilizador.setCurrentIndex(0)
            self.input_email.clear()
            self.carregar_movimentacoes()

            # APENAS um popup centralizado no DashMain
            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done(f"Retirada registrada para a chave '{chave_registro}'!")
        except Exception as e:
            log_acao(
                action="retirada",
                user=user_login,
                resource=chave_registro,
                status="error",
                details=f"Erro ao registrar retirada: utilizador_id={utilizador_id}, email='{email}', erro={e}",
            )
            QMessageBox.critical(self, "Erro", f"Falha ao registrar retirada:\n{e}")

    def _obter_sala_id_por_display(self, display):
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
        user = get_current_user()
        user_login = user["login"] if user else "desconhecido"

        if not selected:
            QMessageBox.warning(self, "Atenção", "Selecione uma movimentação para registrar devolução!")
            log_acao(
                action="devolucao",
                user=user_login,
                status="error",
                details="Tentativa de devolução sem seleção na tabela",
            )
            return

        row = selected[0].row()
        item_id = self.table.item(row, 0)
        if not item_id or not item_id.text().strip().isdigit():
            QMessageBox.warning(self, "Erro", "Registro selecionado não possui ID válido.")
            log_acao(
                action="devolucao",
                user=user_login,
                status="error",
                details="Tentativa de devolução em linha sem ID válido",
            )
            return

        mov_id = int(item_id.text().strip())
        chave_nome = self.table.item(row, 1).text()
        status = self.table.item(row, 6).text()

        if status == "disponível":
            QMessageBox.information(self, "Info", "Esta movimentação já está devolvida!")
            log_acao(
                action="devolucao",
                user=user_login,
                resource=chave_nome,
                status="warning",
                details=f"Tentativa de devolução já devolvida; mov_id={mov_id}",
            )
            return

        sala_id = self._obter_sala_id_por_display(chave_nome)
        if sala_id is None:
            QMessageBox.critical(self, "Erro", "Não foi possível localizar a sala desta movimentação.")
            log_acao(
                action="devolucao",
                user=user_login,
                resource=chave_nome,
                status="error",
                details=f"Erro ao localizar sala para devolução; mov_id={mov_id}",
            )
            return

        try:
            registrar_devolucao(mov_id, chave_nome, sala_id)
            log_acao(
                action="devolucao",
                user=user_login,
                resource=chave_nome,
                status="success",
                details=f"mov_id={mov_id}",
            )

            # atualiza tabela
            self.carregar_movimentacoes()

            # APENAS um popup via DashMain
            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Devolução registrada!")
        except Exception as e:
            log_acao(
                action="devolucao",
                user=user_login,
                resource=chave_nome,
                status="error",
                details=f"Erro ao registrar devolução: mov_id={mov_id}, erro={e}",
            )
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
                writer.writerow(["ID", "Chave", "Utilizador", "E-mail", "Retirada", "Devolução", "Status"])
                for row in dados:
                    row = list(row)
                    row[4] = formatar_data_br(row[4])
                    row[5] = formatar_data_br(row[5])
                    writer.writerow(row)
            QMessageBox.information(self, "Exportação", "Movimentações exportadas para CSV com sucesso!")
            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Exportação CSV concluída")

    def exportar_pdf(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar como PDF", "", "PDF Files (*.pdf)")
        if caminho:
            dados = self.obter_dados_da_tabela()
            c = canvas.Canvas(caminho, pagesize=A4)
            width, height = A4
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "Relatório de Movimentações")
            c.setFont("Helvetica", 12)
            cabecalho = ["ID", "Chave", "Utilizador", "E-mail", "Retirada", "Devolução", "Status"]
            y = height - 80
            c.drawString(50, y, " | ".join(cabecalho))
            y -= 20
            for row in dados:
                row = list(row)
                row[4] = formatar_data_br(row[4])
                row[5] = formatar_data_br(row[5])
                c.drawString(50, y, " | ".join([str(x) if x else "" for x in row]))
                y -= 20
                if y < 50:
                    c.showPage()
                    y = height - 50
            c.save()
            QMessageBox.information(self, "Exportação", "Movimentações exportadas para PDF com sucesso!")
            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Exportação PDF concluída")


def verificar_pendencias_e_enviar_emails():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, chave, usuario, email, data_retirada, alerta_enviado
        FROM movimentacoes
        WHERE status = 'indisponível'
    """)
    rows = cursor.fetchall()
    conn.close()

    now = datetime.now()
    pendencias_encontradas = 0

    for mov_id, chave, usuario, email, data_retirada, alerta_enviado in rows:
        if not data_retirada:
            continue

        try:
            retirada_dt = datetime.strptime(data_retirada, "%Y-%m-%d %H:%M:%S")
            diff_horas = (now - retirada_dt).total_seconds() / 3600
        except Exception as e:
            log_acao(
                action="verificar_pendencias",
                user="sistema",
                resource=chave,
                status="error",
                details=f"Erro ao parsear data_retirada mov_id={mov_id}: {e}",
            )
            continue

        if diff_horas >= ALERTA_HORAS:
            log_acao(
                action="verificar_pendencias",
                user="sistema",
                resource=chave,
                status="warning",
                details=f"Pendência detectada; mov_id={mov_id}, usuario='{usuario}', email='{email}', atraso={diff_horas:.2f}h",
            )
            pendencias_encontradas += 1

    return pendencias_encontradas
