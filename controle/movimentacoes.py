from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QFormLayout, QLineEdit, QComboBox, QHeaderView,
    QMessageBox, QFileDialog, QDateEdit, QDialogButtonBox, QLabel, QToolButton
)
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtCore import Qt, QDate, QTimer
from datetime import datetime, date
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from utils.ui_colors import aplicar_cor_status_item_generico
from utils.validacao import email_valido
from utils.utils import montar_display_sala_por_id
from utils.utils_log import log_acao
from .selecionar_sala_dialog import SelecionarSalaDialog
from autenticacao.helpers_autenticacao import get_db_connection
from autenticacao import get_current_user
import config

from utils.email_service import enviar_email

ALERTA_HORAS = 6


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value

    texto = str(value).strip()
    formatos = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    )

    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt)
        except Exception:
            continue

    try:
        return datetime.fromisoformat(texto.replace("Z", "+00:00"))
    except Exception:
        return None


def _esta_em_atraso(data_retirada, now=None):
    now = now or datetime.now()
    retirada_dt = _parse_datetime(data_retirada)
    if not retirada_dt:
        return False
    diff_horas = (now - retirada_dt).total_seconds() / 3600
    return diff_horas >= ALERTA_HORAS


def _normalizar_status(status):
    if not status:
        return ""
    s = str(status).strip().lower()
    if s in ("disponível", "disponivel"):
        return "disponivel"
    if s in ("indisponível", "indisponivel"):
        return "indisponivel"
    return s


def pode_solicitar_retirada(utilizador_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT vinculo, data_fim_validade, ativo
            FROM utilizadores
            WHERE id = %s
            """,
            (utilizador_id,)
        )
        row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        return False, "Utilizador não encontrado."

    vinculo, data_fim, ativo = row

    if not ativo:
        return False, "Utilizador inativo. Contate o administrador."

    if vinculo == "Servidor(a)" or data_fim is None:
        return True, ""

    hoje = date.today()
    if hoje > data_fim:
        return False, f"Validade expirada em {data_fim.strftime('%d/%m/%Y')}. Contate o administrador."

    return True, ""


def aplicar_cor_status_item(item, status, retirada_val, now):
    status = _normalizar_status(status)
    if not status:
        return

    try:
        if status == "disponivel":
            cor_hex = config.COLOR_STATUS_DISPONIVEL
        elif status == "indisponivel":
            cor_hex = (
                config.COLOR_STATUS_ATRASO
                if _esta_em_atraso(retirada_val, now)
                else config.COLOR_STATUS_INDISPONIVEL
            )
        else:
            return

        item.setBackground(QBrush(QColor(cor_hex)))
    except Exception:
        pass


def formatar_data_br(data_val):
    dt = _parse_datetime(data_val)
    if not dt:
        return "" if data_val is None else str(data_val)
    return dt.strftime("%d/%m/%Y %H:%M:%S")


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

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_filters(self):
        inicio = self.data_inicio.date().toString("yyyy-MM-dd") + " 00:00:00"
        fim = self.data_fim.date().toString("yyyy-MM-dd") + " 23:59:59"
        usuario = self.input_usuario.text().strip().lower() or None
        status = self.combo_status.currentText()
        if status == "Todos":
            status = None
        else:
            status = _normalizar_status(status)
        return {
            "data_ini": inicio,
            "data_fim": fim,
            "usuario": usuario,
            "status": status
        }


def listar_movimentacoes(data_ini=None, data_fim=None):
    conn = get_db_connection()
    try:
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
                m.data_retirada DESC,
                m.data_retorno,
                m.status
        """

        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        conn.close()


def buscar_movimentacoes_personalizado(chave=None, usuario=None, data_ini=None, data_fim=None, status=None):
    conn = get_db_connection()
    try:
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
            query += " AND LOWER(COALESCE(u.nome, m.usuario)) LIKE %s"
            params.append(f"%{usuario.strip().lower()}%")
        if data_ini:
            query += " AND m.data_retirada >= %s"
            params.append(data_ini)
        if data_fim:
            query += " AND m.data_retirada <= %s"
            params.append(data_fim)
        if status and status.lower() not in ["todos", ""]:
            query += " AND m.status = %s"
            params.append(_normalizar_status(status))

        query += """
            ORDER BY
                m.chave,
                s.descricao,
                utilizador,
                u.vinculo,
                m.data_retirada DESC,
                m.data_retorno,
                m.status
        """
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        conn.close()


def registrar_retirada(sala_id, chave_display, utilizador_id, email):
    email = (email or "").strip().lower()
    conn = get_db_connection()

    try:
        cursor = conn.cursor()
        data_retirada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "SELECT nome, ativo FROM utilizadores WHERE id = %s",
            (utilizador_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Utilizador id={utilizador_id} não encontrado")

        nome_utilizador, ativo = row
        if not ativo:
            raise ValueError(f"Utilizador id={utilizador_id} está desativado")
        if not nome_utilizador:
            raise ValueError(f"Utilizador id={utilizador_id} sem nome válido")

        status = "indisponivel"

        cursor.execute(
            """
            INSERT INTO movimentacoes (
                chave, sala_id, utilizador_id, usuario, email, data_retirada, status,
                alerta_enviado, alerta_enviado_em, alerta_erro
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE, NULL, NULL)
            """,
            (chave_display, sala_id, utilizador_id, nome_utilizador, email, data_retirada, status)
        )

        cursor.execute(
            "UPDATE salas SET status = 'indisponivel' WHERE id = %s",
            (sala_id,)
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def registrar_devolucao(mov_id, chave, sala_id):
    conn = get_db_connection()

    try:
        cursor = conn.cursor()
        data_retorno = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "disponivel"

        cursor.execute(
            "UPDATE movimentacoes SET data_retorno = %s, status = %s WHERE id = %s AND chave = %s",
            (data_retorno, status, mov_id, chave)
        )

        cursor.execute(
            "UPDATE salas SET status = 'disponivel' WHERE id = %s",
            (sala_id,)
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class MovimentacoesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.sala_id_atual = None
        self.filtro_atual = None

        self.init_ui()

        try:
            self.carregar_movimentacoes()
        except Exception as e:
            user = get_current_user()
            user_login = user["login"] if user else "sistema"
            log_acao(
                action="init_movimentacoes",
                user=user_login,
                resource="movimentacoes_tab",
                status="error",
                details=f"Erro ao carregar movimentações: {e}",
            )
            QMessageBox.critical(self, "Erro", f"Falha ao carregar movimentações:\n{e}")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.carregar_movimentacoes)
        self.timer.start(5000)

    def _get_dash_main(self):
        janela = self.parentWidget()
        while janela is not None and janela.__class__.__name__ != "DashMain":
            janela = janela.parentWidget()
        return janela

    def _notificar_operacao(self, mensagem):
        dash = self._get_dash_main()
        if dash and hasattr(dash, "show_operation_done"):
            try:
                dash.show_operation_done(mensagem)
            except Exception:
                pass

    def acao_verificar_pendencias(self):
        qtd = verificar_pendencias_e_enviar_emails()
        if qtd > 0:
            QMessageBox.information(
                self, "Pendências", f"Foram encontradas {qtd} pendência(s) em atraso."
            )
        else:
            QMessageBox.information(self, "Pendências", "Nenhuma pendência em atraso encontrada.")

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        layout.addWidget(QLabel("<h2>Movimentações de Chaves/Salas</h2>"))

        form_layout = QHBoxLayout()
        form_layout.setSpacing(10)

        self.label_sala_selecionada = QLineEdit()
        self.label_sala_selecionada.setReadOnly(True)
        self.label_sala_selecionada.setPlaceholderText("Nenhuma sala selecionada")

        self.btn_escolher_sala = QPushButton("Selecionar sala...")
        self.btn_escolher_sala.setObjectName("btnEscolherSala")
        self.btn_escolher_sala.clicked.connect(self.abrir_dialogo_salas)

        form_layout.addWidget(QLabel("Sala:"))
        form_layout.addWidget(self.label_sala_selecionada)
        form_layout.addWidget(self.btn_escolher_sala)

        self.combo_utilizador = QComboBox()
        self.combo_utilizador.setMinimumWidth(220)

        self.btn_novo_utilizador = QToolButton()
        self.btn_novo_utilizador.setText("+ Utilizador")
        self.btn_novo_utilizador.setObjectName("btnNovoUtilizador")
        self.btn_novo_utilizador.setToolTip("Incluir novo utilizador rapidamente")
        self.btn_novo_utilizador.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_novo_utilizador.clicked.connect(self.cadastrar_utilizador_rapido)

        form_layout.addWidget(self.combo_utilizador)
        form_layout.addWidget(self.btn_novo_utilizador)

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
        filter_btn_box.setSpacing(10)

        self.btn_filtrar = QPushButton("Filtrar Movimentações")
        self.btn_filtrar.setObjectName("btnFiltrar")
        self.btn_filtrar.clicked.connect(self.abrir_filtro_modal)
        filter_btn_box.addWidget(self.btn_filtrar)

        self.btn_verificar_pendencias = QPushButton("Verificar pendências")
        self.btn_verificar_pendencias.setObjectName("btnVerificarPendencias")
        self.btn_verificar_pendencias.clicked.connect(self.acao_verificar_pendencias)
        filter_btn_box.addWidget(self.btn_verificar_pendencias)

        layout.addLayout(filter_btn_box)

        export_layout = QHBoxLayout()
        self.btn_exportar_csv = QPushButton("Exportar CSV")
        self.btn_exportar_csv.clicked.connect(self.exportar_csv)
        self.btn_exportar_pdf = QPushButton("Exportar PDF")
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)
        export_layout.addWidget(self.btn_exportar_csv)
        export_layout.addWidget(self.btn_exportar_pdf)
        export_layout.addStretch()
        layout.addLayout(export_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Chave", "Descrição sala", "Utilizador", "Vínculo",
            "Retirada", "Devolução", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setColumnHidden(0, True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.setStyleSheet(f"""
            QPushButton, QToolButton {{
                padding: 8px 16px;
                min-height: 32px;
                border-radius: 5px;
                border: 1px solid #bdbdbd;
                font-weight: 500;
            }}
            QPushButton#btnEscolherSala {{ background-color: #eeeeee; }}
            QPushButton#btnEscolherSala:hover {{ background-color: #e0e0e0; }}

            QPushButton#btnRetirar {{
                background-color: {config.COLOR_BTN_VERDE};
                color: {config.COLOR_BTN_TEXTO};
                border: 1px solid #2e7d32;
            }}
            QPushButton#btnRetirar:hover {{ background-color: #43a047; }}
            QPushButton#btnRetirar:pressed {{ background-color: #2e7d32; }}

            QPushButton#btnDevolver {{
                background-color: {config.COLOR_BTN_AZUL};
                color: {config.COLOR_BTN_TEXTO};
                border: 1px solid #1565c0;
            }}
            QPushButton#btnDevolver:hover {{ background-color: #1976d2; }}
            QPushButton#btnDevolver:pressed {{ background-color: #1565c0; }}

            QPushButton#btnFiltrar, QPushButton#btnVerificarPendencias, QToolButton#btnNovoUtilizador {{
                background-color: {config.COLOR_BTN_LARANJA};
                color: {config.COLOR_BTN_TEXTO_ESCURO};
                border: 1px solid #f57c00;
            }}
            QPushButton#btnFiltrar:hover, QPushButton#btnVerificarPendencias:hover, QToolButton#btnNovoUtilizador:hover {{
                background-color: #ff9800;
            }}
            QPushButton#btnFiltrar:pressed, QPushButton#btnVerificarPendencias:pressed, QToolButton#btnNovoUtilizador:pressed {{
                background-color: #f57c00;
            }}

            QTableWidget {{
                gridline-color: #e0e0e0;
                selection-background-color: #bbdefb;
                selection-color: black;
            }}
            QHeaderView::section {{
                background-color: #f5f5f5;
                padding: 6px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
            }}
        """)

        self.load_utilizadores_combo()

    def abrir_dialogo_salas(self):
        user = get_current_user()
        is_admin = bool(user and user.get("is_admin", False))

        dlg = SelecionarSalaDialog(self, is_admin=is_admin)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        self.sala_id_atual = dlg.sala_id_selecionada
        self.label_sala_selecionada.setText(dlg.sala_display_selecionada or "")

    def load_utilizadores_combo(self):
        self.combo_utilizador.clear()

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, COALESCE(nome, ''), COALESCE(email, '')
                FROM utilizadores
                WHERE ativo = TRUE
                ORDER BY nome
                """
            )
            rows = cur.fetchall()
        finally:
            conn.close()

        self.combo_utilizador.addItem("Selecione o utilizador...", None)
        for uid, nome, email in rows:
            self.combo_utilizador.addItem(nome, {"id": uid, "email": email})

    def cadastrar_utilizador_rapido(self):
        from admin.utilizadores_tab import UtilizadorDialog

        dialog = UtilizadorDialog(self)
        if dialog.exec():
            dados = dialog.get_dados()
            nome = (dados.get("nome", "") or "").strip()
            email = (dados.get("email", "") or "").strip().lower()

            if not nome:
                QMessageBox.warning(self, "Erro", "Nome é obrigatório.")
                return
            if not email:
                QMessageBox.warning(self, "Erro", "E-mail é obrigatório.")
                return
            if not email_valido(email):
                QMessageBox.warning(self, "Erro", "E-mail inválido.")
                return

            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO utilizadores (nome, email, ativo) VALUES (%s, %s, TRUE)",
                    (nome, email)
                )
                conn.commit()
                cur.execute("SELECT currval(pg_get_serial_sequence('utilizadores','id'))")
                novo_id = cur.fetchone()[0]
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Erro", f"Não foi possível cadastrar: {e}")
                return
            finally:
                conn.close()

            self.load_utilizadores_combo()
            for idx in range(self.combo_utilizador.count()):
                dado = self.combo_utilizador.itemData(idx)
                if dado and dado.get("id") == novo_id:
                    self.combo_utilizador.setCurrentIndex(idx)
                    break

            dash = self._get_dash_main()
            if dash and getattr(dash, "util_tab", None):
                try:
                    dash.util_tab.carregar_dados()
                except Exception:
                    pass

            self._notificar_operacao("Utilizador cadastrado com sucesso!")

    def abrir_filtro_modal(self):
        dialog = FiltroMovimentacaoDialog(self)
        if dialog.exec():
            self.filtro_atual = dialog.get_filters()
            resultados = buscar_movimentacoes_personalizado(**self.filtro_atual)
            self.exibir_historico(resultados)

    def carregar_movimentacoes(self):
        if self.filtro_atual is None:
            dados = listar_movimentacoes()
        else:
            dados = buscar_movimentacoes_personalizado(**self.filtro_atual)
        self.exibir_historico(dados)

    def exibir_historico(self, historico):
        self.table.setRowCount(0)
        now = datetime.now()

        for linha_idx, dados in enumerate(historico):
            self.table.insertRow(linha_idx)
            for col_idx, valor in enumerate(dados):
                if isinstance(valor, (bytes, bytearray)):
                    valor = valor.decode("utf-8", errors="ignore")

                if col_idx in (5, 6):
                    valor = formatar_data_br(valor)

                texto = str(valor) if valor is not None else ""
                item = QTableWidgetItem(texto)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                if col_idx == 7:
                    status = _normalizar_status(dados[7])
                    retirada = dados[5]
                    aplicar_cor_status_item_generico(item, status, retirada, dados[6], now)

                self.table.setItem(linha_idx, col_idx, item)

    def adicionar_movimentacao(self):
        sala_id = self.sala_id_atual
        dados_user = self.combo_utilizador.currentData() or {}
        utilizador_id = dados_user.get("id")
        email = (dados_user.get("email", "") or "").strip().lower()
        operador = get_current_user()
        operador_login = operador["login"] if operador else "desconhecido"

        if not sala_id:
            QMessageBox.warning(self, "Atenção", "Selecione uma sala primeiro.")
            return
        if utilizador_id is None:
            QMessageBox.warning(self, "Atenção", "Selecione um utilizador.")
            return

        ok, mensagem = pode_solicitar_retirada(utilizador_id)
        if not ok:
            QMessageBox.warning(self, "Bloqueado", mensagem)
            return

        if email and not email_valido(email):
            QMessageBox.warning(self, "Erro", "E-mail do utilizador é inválido.")
            return

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """SELECT id FROM movimentacoes
                   WHERE sala_id = %s AND status = 'indisponivel' AND data_retorno IS NULL
                   LIMIT 1""",
                (sala_id,)
            )
            if cur.fetchone():
                QMessageBox.warning(
                    self, "Chave já retirada",
                    "Já existe uma retirada em aberto para esta sala. Devolva antes de registrar nova."
                )
                return
        finally:
            conn.close()

        chave = montar_display_sala_por_id(sala_id)
        try:
            registrar_retirada(sala_id, chave, utilizador_id, email)
            log_acao(
                action="retirada", user=operador_login, resource=chave, status="success",
                details=f"utilizador={utilizador_id}, sala={sala_id}"
            )
            self.sala_id_atual = None
            self.label_sala_selecionada.clear()
            self.combo_utilizador.setCurrentIndex(0)
            self.carregar_movimentacoes()
            self._notificar_operacao(f"Retirada registrada: {chave}")
        except Exception as e:
            log_acao(
                action="retirada", user=operador_login, resource=f"sala={sala_id}",
                status="error", details=f"erro: {e}"
            )
            QMessageBox.critical(self, "Erro", f"Falha ao registrar retirada:\n{e}")

    def devolver_selecionada(self):
        itens_selecionados = self.table.selectedItems()
        operador = get_current_user()
        operador_login = operador["login"] if operador else "desconhecido"

        if not itens_selecionados:
            QMessageBox.warning(self, "Atenção", "Selecione uma linha para registrar devolução.")
            return

        linha = itens_selecionados[0].row()
        mov_id = self.table.item(linha, 0).text().strip()
        chave = self.table.item(linha, 1).text().strip()
        status = _normalizar_status(self.table.item(linha, 7).text())

        if not mov_id.isdigit():
            QMessageBox.warning(self, "Erro", "Registro inválido.")
            return
        if status == "disponivel":
            QMessageBox.information(self, "Info", "Esta chave já está devolvida.")
            return

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT sala_id FROM movimentacoes WHERE id = %s", (int(mov_id),))
            sala_id = cur.fetchone()
            if not sala_id:
                QMessageBox.critical(self, "Erro", "Registro não encontrado no banco.")
                return
            sala_id = sala_id[0]
        finally:
            conn.close()

        try:
            registrar_devolucao(int(mov_id), chave, sala_id)
            log_acao(
                action="devolucao", user=operador_login, resource=chave, status="success",
                details=f"mov_id={mov_id}, sala={sala_id}"
            )
            self.carregar_movimentacoes()
            self._notificar_operacao(f"Devolução registrada: {chave}")
        except Exception as e:
            log_acao(
                action="devolucao", user=operador_login, resource=chave,
                status="error", details=f"erro: {e}"
            )
            QMessageBox.critical(self, "Erro", f"Falha ao registrar devolução:\n{e}")

    def obter_dados_da_tabela(self):
        dados = []
        for linha in range(self.table.rowCount()):
            linha_dados = []
            for coluna in range(self.table.columnCount()):
                item = self.table.item(linha, coluna)
                linha_dados.append(item.text() if item else "")
            dados.append(linha_dados)
        return dados

    def exportar_csv(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar como CSV", "", "Arquivo CSV (*.csv)"
        )
        if not caminho:
            return

        dados = self.obter_dados_da_tabela()
        cabecalho = ["ID", "Chave", "Descrição sala", "Utilizador", "Vínculo", "Retirada", "Devolução", "Status"]

        try:
            with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
                escritor = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)
                escritor.writerow(cabecalho)
                escritor.writerows(dados)
            self._notificar_operacao("Arquivo CSV salvo com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao exportar CSV:\n{e}")

    def exportar_pdf(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar como PDF", "", "Arquivo PDF (*.pdf)"
        )
        if not caminho:
            return

        dados = self.obter_dados_da_tabela()
        cabecalho = ["ID", "Chave", "Descrição sala", "Utilizador", "Vínculo", "Retirada", "Devolução", "Status"]
        linhas = [cabecalho] + dados

        estilos = getSampleStyleSheet()
        estilo_celula = estilos["BodyText"]
        estilo_celula.fontName = "Helvetica"
        estilo_celula.fontSize = 8

        try:
            doc = SimpleDocTemplate(
                caminho, pagesize=landscape(A4),
                leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20
            )
            tabela = Table(linhas, repeatRows=1, colWidths=[30, 90, 140, 110, 70, 90, 90, 70])
            tabela.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4285F4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))

            elementos = [
                Paragraph("Relatório de Movimentações de Chaves", estilos["Title"]),
                Spacer(1, 12),
                tabela
            ]
            doc.build(elementos)
            self._notificar_operacao("Arquivo PDF salvo com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao exportar PDF:\n{e}")


def verificar_pendencias_e_enviar_emails():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, chave, usuario, email, data_retirada, alerta_enviado
            FROM movimentacoes
            WHERE status = 'indisponivel' AND data_retorno IS NULL
            """
        )
        linhas = cursor.fetchall()

        agora = datetime.now()
        total_pendencias = 0

        for mov_id, chave, usuario, email, data_retirada, alerta_enviado in linhas:
            if not data_retirada:
                continue

            retirada_dt = _parse_datetime(data_retirada)
            if not retirada_dt:
                log_acao(
                    action="verificar_pendencias", user="sistema", resource=chave,
                    status="error", details=f"Data inválida no registro {mov_id}"
                )
                continue

            horas_atraso = (agora - retirada_dt).total_seconds() / 3600
            if horas_atraso < ALERTA_HORAS:
                continue

            total_pendencias += 1
            if alerta_enviado:
                continue

            if not email:
                cursor.execute(
                    "UPDATE movimentacoes SET alerta_erro = %s WHERE id = %s",
                    ("Sem e-mail cadastrado", mov_id)
                )
                conn.commit()
                continue

            if not email_valido(email):
                cursor.execute(
                    "UPDATE movimentacoes SET alerta_erro = %s WHERE id = %s",
                    (f"E-mail inválido: {email}", mov_id)
                )
                conn.commit()
                continue

            assunto = f"Aviso: Devolução pendente - {chave}"
            corpo = (
                f"Olá, {usuario}!\n\n"
                f"Consta em nosso sistema que a chave/sala '{chave}' foi retirada em "
                f"{formatar_data_br(data_retirada)} e ainda não foi devolvida.\n\n"
                f"Já se passaram {horas_atraso:.1f} horas. Por favor, regularize a devolução o quanto antes.\n\n"
                f"Atenciosamente,\nSistema de Controle de Chaves"
            )

            try:
                enviar_email(email, assunto, corpo)
                cursor.execute(
                    """UPDATE movimentacoes
                       SET alerta_enviado = TRUE, alerta_enviado_em = %s, alerta_erro = NULL
                       WHERE id = %s""",
                    (agora.strftime("%Y-%m-%d %H:%M:%S"), mov_id)
                )
                conn.commit()
                log_acao(
                    action="verificar_pendencias", user="sistema", resource=chave,
                    status="success", details=f"Alerta enviado para {email}"
                )
            except Exception as e:
                conn.rollback()
                cursor.execute(
                    "UPDATE movimentacoes SET alerta_erro = %s WHERE id = %s",
                    (str(e), mov_id)
                )
                conn.commit()
                log_acao(
                    action="verificar_pendencias", user="sistema", resource=chave,
                    status="error", details=f"Erro ao enviar e-mail: {e}"
                )

        return total_pendencias
    finally:
        conn.close()


def ha_chaves_em_atraso():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT data_retirada FROM movimentacoes
               WHERE status = 'indisponivel' AND data_retorno IS NULL"""
        )
        linhas = cursor.fetchall()
    finally:
        conn.close()

    agora = datetime.now()
    qtd = sum(1 for (dt,) in linhas if _esta_em_atraso(dt, agora))
    return qtd > 0, qtd