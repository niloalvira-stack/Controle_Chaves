# controle/movimentacoes.py
import csv
from datetime import datetime, date

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QFormLayout, QLineEdit, QComboBox, QHeaderView,
    QMessageBox, QFileDialog, QDateEdit, QDialogButtonBox, QLabel, QToolButton
)
from PyQt5.QtCore import QDate, QTimer
from PyQt5.QtGui import QBrush, QColor

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from utils.ui_colors import aplicar_cor_status_item_generico
from utils.validacao import email_valido
from utils.utils import montar_display_sala_por_id
from utils.utils_log import log_acao
from .selecionar_sala_dialog import SelecionarSalaDialog
from autenticacao.helpers_autenticacao import get_db_connection
from autenticacao import get_current_user
import config

ALERTA_HORAS = 6


def pode_solicitar_retirada(utilizador_id: int):
    """
    Verifica se o utilizador pode solicitar retirada:
    - precisa estar ativo
    - se vinculo != 'Servidor(a)' e tiver data_fim_validade, não pode estar vencida
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT vinculo, data_fim_validade, ativo
        FROM utilizadores
        WHERE id = %s
    """, (utilizador_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False, "Utilizador não encontrado."

    vinculo, data_fim, ativo = row

    if not ativo:
        return False, "Utilizador inativo. Contate o administrador."

    # Servidor(a) não tem limite de validade
    if vinculo == "Servidor(a)" or data_fim is None:
        return True, ""

    hoje = date.today()
    if hoje > data_fim:
        return False, f"Validade expirada em {data_fim.strftime('%d/%m/%Y')}. Contate o administrador."

    return True, ""


def aplicar_cor_status_item(item, status, retirada_val, now):
    status = (status or "").strip()

    try:
        if status == "disponivel":
            cor_hex = config.COLOR_STATUS_DISPONIVEL

        elif status == "indisponivel":
            atraso = False
            if retirada_val:
                try:
                    if isinstance(retirada_val, datetime):
                        retirada_dt = retirada_val
                    else:
                        retirada_dt = datetime.strptime(str(retirada_val), "%Y-%m-%d %H:%M:%S")
                    diff_horas = (now - retirada_dt).total_seconds() / 3600
                    atraso = diff_horas >= ALERTA_HORAS
                except Exception:
                    atraso = False

            cor_hex = config.COLOR_STATUS_ATRASO if atraso else config.COLOR_STATUS_INDISPONIVEL
        else:
            return

        item.setBackground(QBrush(QColor(cor_hex)))
    except Exception:
        pass


def formatar_data_br(data_str):
    if not data_str:
        return ""
    try:
        return datetime.strptime(str(data_str), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(data_str)


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
        else:
            s = status.strip().lower()
            if s in ("disponível", "disponivel"):
                status = "disponivel"
            elif s in ("indisponível", "indisponivel"):
                status = "indisponivel"
        return {"data_ini": inicio, "data_fim": fim, "usuario": usuario, "status": status}


def listar_movimentacoes(data_ini=None, data_fim=None):
    """
    Lista movimentações, por padrão apenas do dia atual.
    Se data_ini/data_fim forem informadas, usa o intervalo.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT
               m.id,
               m.chave,
               s.descricao,
               COALESCE(u.nome, m.usuario) AS utilizador,
               u.vinculo,
               m.data_retirada,
               m.data_retorno,
               m.status
        FROM movimentacoes m
        LEFT JOIN utilizadores u ON u.id = m.utilizador_id
        LEFT JOIN salas s        ON s.id = m.sala_id
        WHERE 1=1
    """
    params = []

    if data_ini is None and data_fim is None:
        # somente movimentações do dia atual
        query += " AND m.data_retirada::date = CURRENT_DATE"
    else:
        if data_ini:
            query += " AND m.data_retirada >= %s"
            params.append(data_ini)
        if data_fim:
            query += " AND m.data_retirada <= %s"
            params.append(data_fim)

    query += """
        ORDER BY
            m.chave,
            s.descricao,
            utilizador,
            u.vinculo,
            m.data_retirada,
            m.data_retorno,
            m.status
    """

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def buscar_movimentacoes_personalizado(chave=None, usuario=None, data_ini=None, data_fim=None, status=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT
               m.id,
               m.chave,
               s.descricao,
               COALESCE(u.nome, m.usuario) AS utilizador,
               u.vinculo,
               m.data_retirada,
               m.data_retorno,
               m.status
        FROM movimentacoes m
        LEFT JOIN utilizadores u ON u.id = m.utilizador_id
        LEFT JOIN salas s        ON s.id = m.sala_id
        WHERE 1=1
    """
    params = []
    if chave:
        query += " AND m.chave ILIKE %s"
        params.append(f"%{chave}%")
    if usuario:
        usuario = usuario.strip().lower()
        query += " AND LOWER(COALESCE(u.nome, m.usuario)) LIKE %s"
        params.append(f"%{usuario}%")
    if data_ini:
        query += " AND (m.data_retirada >= %s)"
        params.append(data_ini)
    if data_fim:
        query += " AND (m.data_retirada <= %s)"
        params.append(data_fim)
    if status and status.lower() not in ["todos", ""]:
        query += " AND m.status = %s"
        params.append(status)

    query += """
        ORDER BY
            m.chave,
            s.descricao,
            utilizador,
            u.vinculo,
            m.data_retirada,
            m.data_retorno,
            m.status
    """
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def registrar_retirada(sala_id, chave_display, utilizador_id, email):
    email = (email or "").strip().lower()

    conn = get_db_connection()
    cursor = conn.cursor()
    data_retirada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "SELECT nome, ativo FROM utilizadores WHERE id = %s",
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

    status = "indisponivel"

    cursor.execute(
        """
        INSERT INTO movimentacoes (
            chave, sala_id, utilizador_id, usuario, email, data_retirada, status, alerta_enviado
        )
        VALUES (%s,   %s,      %s,           %s,      %s,    %s,            %s,    FALSE)
        """,
        (chave_display, sala_id, utilizador_id, nome_utilizador, email, data_retirada, status)
    )

    cursor.execute(
        "UPDATE salas SET status = 'indisponivel' WHERE id = %s",
        (sala_id,)
    )

    conn.commit()
    conn.close()


def registrar_devolucao(mov_id, chave, sala_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    data_retorno = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    status = "disponivel"

    cursor.execute(
        "UPDATE movimentacoes SET data_retorno=%s, status=%s WHERE id=%s AND chave=%s",
        (data_retorno, status, mov_id, chave)
    )

    cursor.execute(
        "UPDATE salas SET status = 'disponivel' WHERE id = %s",
        (sala_id,)
    )

    conn.commit()
    conn.close()


class MovimentacoesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.sala_id_atual = None
        self.filtro_atual = None  # None = hoje; dict = filtro personalizado

        self.init_ui()

        try:
            # carrega apenas movimentações do dia ao iniciar
            self.carregar_movimentacoes()
        except Exception as e:
            user = get_current_user()
            user_login = user["login"] if user else "sistema"
            log_acao(
                action="init_movimentacoes",
                user=user_login,
                status="error",
                details=f"Erro ao carregar movimentações: {e}",
            )
            QMessageBox.critical(self, "Erro", f"Falha ao carregar movimentações:\n{e}")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.carregar_movimentacoes)
        self.timer.start(5000)

    def _get_dash_main(self):
        from interface.dash_main import DashMain
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
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Chave", "Descrição sala", "Utilizador", "Vínculo", "Retirada", "Devolução", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setColumnHidden(0, True)
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 24px;
                min-height: 34px;
                min-width: 140px;
                border-radius: 6px;
                border: 1px solid #888;
                font-weight: 500;
            }}
            QPushButton#btnEscolherSala {{
                background-color: #eeeeee;
            }}
            QPushButton#btnEscolherSala:hover {{
                background-color: #f5f5f5;
            }}
            QPushButton#btnRetirar {{
                background-color: {config.COLOR_BTN_VERDE};
                color: {config.COLOR_BTN_TEXTO};
                border: 1px solid #1b5e20;
            }}
            QPushButton#btnRetirar:hover {{
                background-color: #388e3c;
            }}
            QPushButton#btnRetirar:pressed {{
                background-color: #1b5e20;
            }}
            QPushButton#btnDevolver {{
                background-color: {config.COLOR_BTN_AZUL};
                color: {config.COLOR_BTN_TEXTO};
                border: 1px solid #0d47a1;
            }}
            QPushButton#btnDevolver:hover {{
                background-color: #1976d2;
            }}
            QPushButton#btnDevolver:pressed {{
                background-color: #0d47a1;
            }}
            QPushButton#btnFiltrar, QPushButton#btnVerificarPendencias {{
                background-color: {config.COLOR_BTN_LARANJA};
                color: {config.COLOR_BTN_TEXTO_ESCURO};
                border: 1px solid #f57f17;
            }}
            QPushButton#btnFiltrar:hover, QPushButton#btnVerificarPendencias:hover {{
                background-color: #fbc02d;
            }}
            QPushButton#btnFiltrar:pressed, QPushButton#btnVerificarPendencias:pressed {{
                background-color: #f57f17;
            }}
        """)

        self.load_utilizadores_combo()

    def abrir_dialogo_salas(self):
        dlg = SelecionarSalaDialog(self)
        result = dlg.exec()
        if result != QDialog.Accepted:
            return

        sala_id = dlg.sala_id_selecionada
        sala_display = dlg.sala_display_selecionada

        if sala_id is None or not sala_display:
            QMessageBox.warning(self, "Atenção", "Nenhuma sala foi selecionada.")
            return

        self.sala_id_atual = sala_id
        self.label_sala_selecionada.setText(sala_display)

    def load_utilizadores_combo(self):
        self.combo_utilizador.clear()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, COALESCE(nome, '') AS nome, COALESCE(email, '') AS email
            FROM utilizadores
            WHERE ativo = TRUE
            ORDER BY nome
        """)
        rows = cur.fetchall()
        conn.close()

        self.combo_utilizador.addItem("Selecione o utilizador...", None)

        for row in rows:
            uid = row[0]
            nome = row[1] or ""
            email = row[2] or ""

            if email:
                display = f"{nome} ({email})"
            else:
                display = nome

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
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO utilizadores (nome, email, ativo) VALUES (%s, %s, TRUE)",
                    (nome, email),
                )
                conn.commit()

                cur.execute("SELECT currval(pg_get_serial_sequence('utilizadores','id'))")
                novo_id = cur.fetchone()[0]
                conn.close()

                self.load_utilizadores_combo()
                for idx in range(self.combo_utilizador.count()):
                    if self.combo_utilizador.itemData(idx) == novo_id:
                        self.combo_utilizador.setCurrentIndex(idx)
                        break

                dash = self._get_dash_main()
                if dash is not None and getattr(dash, "util_tab", None) is not None:
                    try:
                        dash.util_tab.load_utilizadores()
                    except Exception:
                        pass

                if dash is not None:
                    dash.show_operation_done("Utilizador cadastrado")

            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cadastrar utilizador:\n{e}")

    def abrir_filtro_modal(self):
        dialog = FiltroMovimentacaoDialog(self)
        if dialog.exec():
            filtros = dialog.get_filters()
            # guarda filtro atual para o timer e para manter o grid
            self.filtro_atual = filtros
            resultados = buscar_movimentacoes_personalizado(
                None,
                filtros["usuario"],
                filtros["data_ini"],
                filtros["data_fim"],
                filtros["status"],
            )
            self.exibir_historico(resultados)

    def carregar_movimentacoes(self):
        """
        Recarrega o grid respeitando o filtro atual:
        - None: apenas movimentações do dia (DEFAULT)
        - dict em self.filtro_atual: usa o filtro personalizado
        """
        if self.filtro_atual is None:
            historico = listar_movimentacoes()
        else:
            f = self.filtro_atual
            historico = buscar_movimentacoes_personalizado(
                None,
                f["usuario"],
                f["data_ini"],
                f["data_fim"],
                f["status"],
            )
        self.exibir_historico(historico)

    def exibir_historico(self, historico):
        self.table.setRowCount(0)
        now = datetime.now()

        for row_idx, row_data in enumerate(historico):
            self.table.insertRow(row_idx)

            for col_idx, value in enumerate(row_data):
                if isinstance(value, (bytes, bytearray)):
                    value = value.decode("utf-8", errors="ignore")

                if col_idx in [5, 6]:
                    value = formatar_data_br(value)

                texto = value if value is not None else ""
                item = QTableWidgetItem(str(texto))

                if col_idx == 7:
                    status = row_data[7]
                    if isinstance(status, (bytes, bytearray)):
                        status = status.decode("utf-8", errors="ignore")

                    retirada_val = row_data[5]
                    retorno_val = row_data[6]
                    aplicar_cor_status_item_generico(item, status, retirada_val, retorno_val, now)

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

        ok, msg = pode_solicitar_retirada(utilizador_id)
        if not ok:
            QMessageBox.warning(self, "Bloqueado", msg)
            log_acao(
                action="retirada",
                user=user_login,
                resource=f"sala_id={sala_id}",
                status="warning",
                details=f"Bloqueado por validade: utilizador_id={utilizador_id}, motivo='{msg}'",
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

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id
            FROM movimentacoes
            WHERE sala_id = %s
              AND status = 'indisponivel'
              AND data_retorno IS NULL
            ORDER BY data_retirada DESC
            LIMIT 1
        """, (sala_id,))
        mov_aberta = cur.fetchone()
        conn.close()

        if mov_aberta:
            QMessageBox.warning(
                self,
                "Chave já retirada",
                "Já existe uma retirada em aberto para esta chave/sala.\n"
                "Efetue a devolução antes de registrar nova retirada."
            )
            log_acao(
                action="retirada",
                user=user_login,
                resource=f"sala_id={sala_id}",
                status="warning",
                details=f"Tentativa de retirada com movimentação em aberto; utilizador_id={utilizador_id}",
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

            self.sala_id_atual = None
            self.label_sala_selecionada.clear()
            self.combo_utilizador.setCurrentIndex(0)
            self.input_email.clear()
            self.carregar_movimentacoes()

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
        conn = get_db_connection()
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
            QMessageBox.warning(self, "Atencao", "Selecione uma movimentacao para registrar devolucao!")
            log_acao(
                action="devolucao",
                user=str(user_login),
                status="error",
                details="Tentativa de devolucao sem selecao na tabela",
            )
            return

        row = selected[0].row()
        item_id = self.table.item(row, 0)
        if not item_id or not item_id.text().strip().isdigit():
            QMessageBox.warning(self, "Erro", "Registro selecionado nao possui ID valido.")
            log_acao(
                action="devolucao",
                user=str(user_login),
                status="error",
                details="Tentativa de devolucao em linha sem ID valido",
            )
            return

        mov_id = int(item_id.text().strip())
        chave_nome = self.table.item(row, 1).text()
        status = self.table.item(row, 7).text()

        if status.strip().lower() in ("disponível", "disponivel"):
            QMessageBox.information(self, "Info", "Esta movimentacao ja esta devolvida!")
            log_acao(
                action="devolucao",
                user=str(user_login),
                resource=str(chave_nome),
                status="warning",
                details=f"Tentativa de devolucao ja devolvida; mov_id={mov_id}",
            )
            return

        # NOVO: buscar sala_id direto no banco pela movimentacao
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sala_id FROM movimentacoes WHERE id = %s", (mov_id,))
        row_db = cursor.fetchone()
        conn.close()

        if not row_db or row_db[0] is None:
            QMessageBox.critical(self, "Erro", "Nao foi possivel localizar a sala desta movimentacao.")
            log_acao(
                action="devolucao",
                user=str(user_login),
                resource=str(chave_nome),
                status="error",
                details=f"Erro ao localizar sala para devolucao; mov_id={mov_id}",
            )
            return

        sala_id = row_db[0]

        try:
            registrar_devolucao(mov_id, chave_nome, sala_id)
            log_acao(
                action="devolucao",
                user=str(user_login),
                resource=str(chave_nome),
                status="success",
                details=f"mov_id={mov_id}",
            )

            self.carregar_movimentacoes()

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Devolucao registrada!")
        except Exception as e:
            ...

            pass

            QMessageBox.critical(
                self,
                "Erro",
                "Falha ao registrar devolucao. Verifique o log para mais detalhes."
            )

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
                writer.writerow(["ID", "Chave", "Descrição sala", "Utilizador", "Vínculo", "Retirada", "Devolução", "Status"])
                for row in dados:
                    row = list(row)
                    row[5] = formatar_data_br(row[5])
                    row[6] = formatar_data_br(row[6])
                    writer.writerow(row)

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
            cabecalho = ["ID", "Chave", "Descrição sala", "Utilizador", "Vínculo", "Retirada", "Devolução", "Status"]
            y = height - 80
            c.drawString(50, y, " | ".join(cabecalho))
            y -= 20
            for row in dados:
                row = list(row)
                row[5] = formatar_data_br(row[5])
                row[6] = formatar_data_br(row[6])
                c.drawString(50, y, " | ".join([str(x) if x else "" for x in row]))
                y -= 20
                if y < 50:
                    c.showPage()
                    y = height - 50
            c.save()

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Exportação PDF concluída")


def verificar_pendencias_e_enviar_emails():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, chave, usuario, email, data_retirada, alerta_enviado
        FROM movimentacoes
        WHERE status = 'indisponivel'
    """)
    rows = cursor.fetchall()
    conn.close()

    now = datetime.now()
    pendencias_encontradas = 0

    for mov_id, chave, usuario, email, data_retirada, alerta_enviado in rows:
        if not data_retirada:
            continue

        try:
            if isinstance(data_retirada, datetime):
                retirada_dt = data_retirada
            else:
                retirada_dt = datetime.strptime(str(data_retirada), "%Y-%m-%d %H:%M:%S")
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
