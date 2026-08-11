from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QFormLayout, QLineEdit, QComboBox, QHeaderView,
    QMessageBox, QFileDialog, QDateEdit, QDialogButtonBox, QLabel, QToolButton,
    QAbstractItemView
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

ALERTA_HORAS = 12

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


def _normalizar_motivo_emprestimo(motivo):
    if motivo is None:
        return None
    m = str(motivo).strip().lower()
    if not m:
        return None
    permitidos = {
        "normal",
        "copia_temporaria",
        "extravio",
        "nao_devolvida",
        "contingencia",
    }
    if m not in permitidos:
        raise ValueError(f"Motivo de empréstimo inválido: {motivo}")
    return m


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

    if str(vinculo or "").strip() == "Servidor(a)" or data_fim is None:
        return True, ""

    hoje = date.today()
    if hoje > data_fim:
        return False, f"Validade expirada em {data_fim.strftime('%d/%m/%Y')}. Contate o administrador."

    return True, ""


def formatar_data_br(data_val):
    dt = _parse_datetime(data_val)
    if not dt:
        return "" if data_val is None else str(data_val)
    return dt.strftime("%d/%m/%Y %H:%M:%S")


def obter_chave_fisica_disponivel_por_sala(sala_id, apenas_principal=False):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        query = """
            SELECT id, etiqueta, tipo, status
            FROM chaves_fisicas
            WHERE sala_id = %s
              AND ativa = TRUE
              AND status = 'disponivel'
        """
        params = [sala_id]

        if apenas_principal:
            query += " AND tipo = 'principal' LIMIT 1"
        else:
            # Busca PRIMEIRO a principal, DEPOIS a reserva/cópia, pega a primeira disponível
            query += """
                ORDER BY
                    CASE tipo
                        WHEN 'principal' THEN 0
                        WHEN 'reserva' THEN 1
                        ELSE 2
                    END,
                    id
                LIMIT 1
            """

        cur.execute(query, params)
        return cur.fetchone()
    finally:
        conn.close()


def pode_retirar_chave_fisica(chave_fisica_id):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, ativa, status
            FROM chaves_fisicas
            WHERE id = %s
            """,
            (chave_fisica_id,)
        )
        row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return False, "Chave física não encontrada."

    _, ativa, status = row
    if not ativa:
        return False, "Chave física inativa."
    if _normalizar_status(status) != "disponivel":
        return False, "Chave física não está disponível."
    return True, ""


def listar_movimentacoes(data_ini=None, data_fim=None):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT
                m.id,
                COALESCE(cf.etiqueta, m.chave, '') AS chave_display,
                m.chave_fisica_id,
                CASE
                    WHEN COALESCE(s.nome, '') <> '' AND COALESCE(s.descricao, '') <> ''
                        THEN s.nome || ' - ' || s.descricao
                    WHEN COALESCE(s.nome, '') <> ''
                        THEN s.nome
                    ELSE COALESCE(s.descricao, '')
                END AS sala_display,
                COALESCE(u.nome, m.usuario) AS utilizador,
                u.vinculo,
                m.data_retirada,
                m.data_retorno,
                m.status,
                cf.tipo,
                m.motivo_emprestimo,
                s.id AS sala_id,
                m.alerta_enviado
            FROM movimentacoes m
            LEFT JOIN utilizadores u ON u.id = m.utilizador_id
            LEFT JOIN salas s ON s.id = m.sala_id
            LEFT JOIN chaves_fisicas cf ON cf.id = m.chave_fisica_id
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
                chave_display,
                sala_display,
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
                COALESCE(cf.etiqueta, m.chave, '') AS chave_display,
                m.chave_fisica_id,
                CASE
                    WHEN COALESCE(s.nome, '') <> '' AND COALESCE(s.descricao, '') <> ''
                        THEN s.nome || ' - ' || s.descricao
                    WHEN COALESCE(s.nome, '') <> ''
                        THEN s.nome
                    ELSE COALESCE(s.descricao, '')
                END AS sala_display,
                COALESCE(u.nome, m.usuario) AS utilizador,
                u.vinculo,
                m.data_retirada,
                m.data_retorno,
                m.status,
                cf.tipo,
                m.motivo_emprestimo,
                s.id AS sala_id,
                m.alerta_enviado
            FROM movimentacoes m
            LEFT JOIN utilizadores u ON u.id = m.utilizador_id
            LEFT JOIN salas s ON s.id = m.sala_id
            LEFT JOIN chaves_fisicas cf ON cf.id = m.chave_fisica_id
            WHERE 1=1
        """
        params = []

        if chave:
            query += " AND COALESCE(cf.etiqueta, m.chave, '') ILIKE %s"
            params.append(f"%{chave.strip()}%")

        if usuario:
            query += " AND COALESCE(u.nome, m.usuario) ILIKE %s"
            params.append(f"%{usuario.strip()}%")

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
                chave_display,
                sala_display,
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


def salas_com_pelo_menos_uma_copia():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT sala_id
            FROM chaves_fisicas
            WHERE ativa = TRUE
              AND tipo = 'reserva'
            """
        )
        return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()


def registrar_retirada(sala_id, chave_fisica_id, utilizador_id, email, motivo_emprestimo=None):
    email = (email or "").strip().lower()
    motivo_emprestimo = _normalizar_motivo_emprestimo(motivo_emprestimo)
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

        cursor.execute(
            """
            SELECT id, sala_id, etiqueta, ativa, status
            FROM chaves_fisicas
            WHERE id = %s
            FOR UPDATE
            """,
            (chave_fisica_id,)
        )
        chave_row = cursor.fetchone()
        if not chave_row:
            raise ValueError(f"Chave física id={chave_fisica_id} não encontrada")

        _, sala_id_chave, etiqueta, ativa, status_chave = chave_row
        if sala_id_chave != sala_id:
            raise ValueError("A chave física selecionada não pertence à sala informada")
        if not ativa:
            raise ValueError("Chave física inativa")
        if _normalizar_status(status_chave) != "disponivel":
            raise ValueError("Chave física não está disponível")

        cursor.execute(
            """
            SELECT id FROM movimentacoes
            WHERE chave_fisica_id = %s
              AND status = 'indisponivel'
              AND data_retorno IS NULL
            LIMIT 1
            """,
            (chave_fisica_id,)
        )
        if cursor.fetchone():
            raise ValueError("Já existe uma retirada em aberto para esta chave física")

        status = "indisponivel"
        chave_display = etiqueta or montar_display_sala_por_id(sala_id)

        cursor.execute(
            """
            INSERT INTO movimentacoes (
                chave, chave_fisica_id, sala_id, utilizador_id, usuario, email,
                data_retirada, status, alerta_enviado, alerta_enviado_em,
                alerta_erro, motivo_emprestimo
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE, NULL, NULL, %s)
            """,
            (
                chave_display,
                chave_fisica_id,
                sala_id,
                utilizador_id,
                nome_utilizador,
                email,
                data_retirada,
                status,
                motivo_emprestimo
            )
        )

        cursor.execute(
            "UPDATE salas SET status = 'indisponivel' WHERE id = %s",
            (sala_id,)
        )

        cursor.execute(
            "UPDATE chaves_fisicas SET status = 'indisponivel', atualizada_em = CURRENT_TIMESTAMP WHERE id = %s",
            (chave_fisica_id,)
        )

        conn.commit()
        return chave_display
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def registrar_devolucao(mov_id, sala_id=None):
    conn = get_db_connection()

    try:
        cursor = conn.cursor()
        data_retorno = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "disponivel"

        cursor.execute(
            """
            SELECT chave, chave_fisica_id, sala_id, status
            FROM movimentacoes
            WHERE id = %s
            FOR UPDATE
            """,
            (mov_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Movimentação id={mov_id} não encontrada")

        chave, chave_fisica_id, sala_id_db, status_atual = row
        if _normalizar_status(status_atual) == "disponivel":
            return chave or "", chave_fisica_id, sala_id_db

        sala_id_final = sala_id_db if sala_id is None else sala_id

        cursor.execute(
            """
            UPDATE movimentacoes
            SET data_retorno = %s, status = %s, alerta_enviado = FALSE
            WHERE id = %s
            """,
            (data_retorno, status, mov_id)
        )

        if sala_id_final is not None:
            cursor.execute(
                "UPDATE salas SET status = 'disponivel' WHERE id = %s",
                (sala_id_final,)
            )

        if chave_fisica_id is not None:
            cursor.execute(
                "UPDATE chaves_fisicas SET status = 'disponivel', atualizada_em = CURRENT_TIMESTAMP WHERE id = %s",
                (chave_fisica_id,)
            )

        conn.commit()
        return chave or "", chave_fisica_id, sala_id_final
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


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


class MovimentacoesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.sala_id_atual = None
        self.filtro_atual = None
        self.chave_fisica_id_atual = None
        self._em_operacao = False
        self.filtro_apenas_copias = False

        self.utilizador_atual = get_current_user()
        self.eh_admin = bool(self.utilizador_atual and self.utilizador_atual.get("is_admin", False))

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

    def _preservar_mov_id_selecionado(self):
        selecionadas = self.table.selectionModel().selectedRows()
        if not selecionadas:
            return None
        linha = selecionadas[0].row()
        item = self.table.item(linha, 0)
        return item.text().strip() if item else None

    def _restaurar_selecao_por_mov_id(self, mov_id):
        if not mov_id:
            return
        for linha in range(self.table.rowCount()):
            item = self.table.item(linha, 0)
            if item and item.text().strip() == str(mov_id):
                self.table.selectRow(linha)
                break

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

        self.combo_motivo = QComboBox()
        self.combo_motivo.addItem("Normal", "normal")
        self.combo_motivo.addItem("Cópia temporária", "copia_temporaria")
        self.combo_motivo.addItem("Extravio", "extravio")
        self.combo_motivo.addItem("Não devolvida", "nao_devolvida")
        self.combo_motivo.addItem("Contingência", "contingencia")
        form_layout.addWidget(QLabel("Motivo:"))
        form_layout.addWidget(self.combo_motivo)

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

        colunas = [
            "ID", "Chave", "Chave física ID", "Descrição sala", "Utilizador", "Vínculo",
            "Retirada", "Devolução", "Status", "Tipo", "Motivo", "Aviso"
        ]
        if not self.eh_admin:
            colunas.pop(9)

        self.table = QTableWidget()
        self.table.setColumnCount(len(colunas))
        self.table.setHorizontalHeaderLabels(colunas)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setColumnHidden(0, True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
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

        if dlg.sala_id_selecionada is None:
            QMessageBox.warning(self, "Aviso", "Nenhuma sala válida foi selecionada.")
            return

        self.sala_id_atual = dlg.sala_id_selecionada
        self.label_sala_selecionada.setText(dlg.sala_display_selecionada or "")

        if is_admin and dlg.apenas_copias_reserva:
            self.filtro_apenas_copias = True
            busca_apenas_principal = True  # Se quiser pegar só cópias quando o botão estiver marcado
        else:
            self.filtro_apenas_copias = False
            busca_apenas_principal = False  # Agora busca QUALQUER chave disponível

        chave_row = obter_chave_fisica_disponivel_por_sala(
            self.sala_id_atual,
            apenas_principal=busca_apenas_principal
        )
        self.chave_fisica_id_atual = chave_row[0] if chave_row else None

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
                    """
                    INSERT INTO utilizadores (nome, email, ativo)
                    VALUES (%s, %s, TRUE)
                    RETURNING id
                    """,
                    (nome, email)
                )
                novo_id = cur.fetchone()[0]
                conn.commit()
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
            self.carregar_movimentacoes()

    def carregar_movimentacoes(self):
        if self._em_operacao:
            return
        try:
            mov_id_sel = self._preservar_mov_id_selecionado() if hasattr(self, "table") else None

            if self.filtro_atual is None:
                dados = listar_movimentacoes()
            else:
                dados = buscar_movimentacoes_personalizado(**self.filtro_atual)

            if self.eh_admin and self.filtro_apenas_copias:
                salas_com_copia = salas_com_pelo_menos_uma_copia()
                dados = [linha for linha in dados if linha[12] in salas_com_copia]

            self.exibir_historico(dados)
            self._restaurar_selecao_por_mov_id(mov_id_sel)
        except Exception as e:
            user = get_current_user()
            user_login = user["login"] if user else "sistema"
            log_acao(
                action="carregar_movimentacoes",
                user=user_login,
                resource="movimentacoes_tab",
                status="error",
                details=f"Erro ao atualizar lista: {e}"
            )

    def exibir_historico(self, historico):
        self.table.setRowCount(0)
        now = datetime.now()

        for linha_idx, dados in enumerate(historico):
            dados = list(dados)
            alerta_enviado = dados.pop()

            if not self.eh_admin:
                dados.pop(9)

            self.table.insertRow(linha_idx)
            for col_idx, valor in enumerate(dados):
                if isinstance(valor, (bytes, bytearray)):
                    valor = valor.decode("utf-8", errors="ignore")

                if col_idx in (6, 7):
                    valor = formatar_data_br(valor)

                texto = str(valor) if valor is not None else ""
                item = QTableWidgetItem(texto)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                coluna_status = 8
                if col_idx == coluna_status:
                    status = _normalizar_status(dados[coluna_status])
                    retirada = dados[6]
                    devolucao = dados[7]

                    # Primeiro aplica a cor padrão (disponível/indisponível normal)
                    aplicar_cor_status_item_generico(item, status, retirada, devolucao, now)

                    # Aplica VERMELHO SOMENTE se: indisponível E passou de 12h
                    if status == "indisponivel" and _esta_em_atraso(retirada, now):
                        item.setBackground(QBrush(QColor("#ffcccc")))
                        item.setForeground(QBrush(QColor("#b71c1c")))

                self.table.setItem(linha_idx, col_idx, item)

            coluna_aviso = self.table.columnCount() - 1
            item_aviso = QTableWidgetItem()
            if alerta_enviado:
                item_aviso.setText("✅")
                item_aviso.setToolTip("Aviso de atraso já enviado por e-mail")
            else:
                item_aviso.setText("❌")
                item_aviso.setToolTip("Aviso ainda não enviado")
            item_aviso.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(linha_idx, coluna_aviso, item_aviso)

    def adicionar_movimentacao(self):
        sala_id = self.sala_id_atual
        dados_user = self.combo_utilizador.currentData() or {}
        utilizador_id = dados_user.get("id")
        email = (dados_user.get("email", "") or "").strip().lower()
        motivo_emprestimo = self.combo_motivo.currentData()
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

        chave_row = obter_chave_fisica_disponivel_por_sala(
            sala_id,
            apenas_principal = not self.filtro_apenas_copias
        )
        if not chave_row:
            tipo_chave = "cópia/reserva" if self.filtro_apenas_copias else "principal"
            QMessageBox.warning(
                self,
                "Sem chave disponível",
                f"Nenhuma chave {tipo_chave} disponível para esta sala."
            )
            return

        chave_fisica_id = chave_row[0]
        ok, mensagem = pode_retirar_chave_fisica(chave_fisica_id)
        if not ok:
            QMessageBox.warning(self, "Atenção", mensagem)
            return

        self._em_operacao = True
        self.timer.stop()
        try:
            chave = registrar_retirada(sala_id, chave_fisica_id, utilizador_id, email, motivo_emprestimo)
            log_acao(
                action="retirada", user=operador_login, resource=chave, status="success",
                details=f"utilizador={utilizador_id}, sala={sala_id}, chave_fisica_id={chave_fisica_id}, motivo={motivo_emprestimo}"
            )
            self.sala_id_atual = None
            self.chave_fisica_id_atual = None
            self.label_sala_selecionada.clear()
            self.combo_utilizador.setCurrentIndex(0)
            self.combo_motivo.setCurrentIndex(0)
            self.carregar_movimentacoes()
            self._notificar_operacao(f"Retirada registrada: {chave}")
        except Exception as e:
            log_acao(
                action="retirada", user=operador_login, resource=f"sala={sala_id}",
                status="error", details=f"erro: {e}"
            )
            QMessageBox.critical(self, "Erro", f"Falha ao registrar retirada:\n{e}")
        finally:
            self._em_operacao = False
            self.timer.start(5000)

    def devolver_selecionada(self):
        selecionadas = self.table.selectionModel().selectedRows()
        operador = get_current_user()
        operador_login = operador["login"] if operador else "desconhecido"

        if not selecionadas:
            QMessageBox.warning(self, "Atenção", "Selecione uma linha para registrar devolução.")
            return

        linha = selecionadas[0].row()
        mov_id = self.table.item(linha, 0).text().strip()
        chave = self.table.item(linha, 1).text().strip()
        status = _normalizar_status(self.table.item(linha, 8).text())

        if not mov_id.isdigit():
            QMessageBox.warning(self, "Erro", "Registro inválido.")
            return
        if status == "disponivel":
            QMessageBox.information(self, "Info", "Esta chave já está devolvida.")
            return

        self._em_operacao = True
        self.timer.stop()
        try:
            chave, chave_fisica_id, sala_id = registrar_devolucao(int(mov_id))
            log_acao(
                action="devolucao", user=operador_login, resource=chave, status="success",
                details=f"mov_id={mov_id}, sala={sala_id}, chave_fisica_id={chave_fisica_id}"
            )
            self.carregar_movimentacoes()
            self._notificar_operacao(f"Devolução registrada: {chave}")
        except Exception as e:
            log_acao(
                action="devolucao", user=operador_login, resource=chave,
                status="error", details=f"erro: {e}"
            )
            QMessageBox.critical(self, "Erro", f"Falha ao registrar devolução:\n{e}")
        finally:
            self._em_operacao = False
            self.timer.start(5000)

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
        cabecalho = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]

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
        cabecalho = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]

        estilos = getSampleStyleSheet()
        estilo_celula = estilos["BodyText"]
        estilo_celula.fontName = "Helvetica"
        estilo_celula.fontSize = 8
        estilo_celula.leading = 10

        try:
            linhas = [cabecalho]
            for linha in dados:
                linhas.append([
                    Paragraph(str(c).replace("&", "&amp;") if c is not None else "", estilo_celula)
                    for c in linha
                ])

            doc = SimpleDocTemplate(
                caminho, pagesize=landscape(A4),
                leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20
            )
            larguras = [28, 80, 55, 130, 100, 70, 85, 85, 70, 55, 85, 50] if self.eh_admin else [28, 80, 55, 130, 100, 70, 85, 85, 70, 85, 50]
            tabela = Table(linhas, repeatRows=1, colWidths=larguras)
            tabela.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4285F4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
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
    total_pendencias = 0
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.id, m.chave, m.usuario, u.email, m.data_retirada, m.alerta_enviado
            FROM movimentacoes m
            LEFT JOIN utilizadores u ON m.utilizador_id = u.id
            WHERE m.status = 'indisponivel' AND m.data_retorno IS NULL
            """
        )
        linhas = cursor.fetchall()
        agora = datetime.now()

        for mov_id, chave, usuario, email, data_retirada, alerta_enviado in linhas:
            if not data_retirada:
                continue

            retirada_dt = _parse_datetime(data_retirada)
            if not retirada_dt:
                log_acao("verificar_pendencias", "sistema", chave, "error", f"Data inválida mov={mov_id}")
                continue

            horas_atraso = (agora - retirada_dt).total_seconds() / 3600
            if horas_atraso < ALERTA_HORAS:
                continue

            total_pendencias += 1
            if alerta_enviado:
                continue

            log_acao(
                "verificar_pendencias", "sistema", chave, "info",
                f"Encontrado: usuario={usuario} | email_encontrado='{email}' | horas={horas_atraso:.1f}"
            )

            if not email:
                msg_erro = "E-mail não cadastrado no perfil do utilizador"
                cursor.execute("UPDATE movimentacoes SET alerta_erro = %s WHERE id = %s", (msg_erro, mov_id))
                conn.commit()
                log_acao("verificar_pendencias", "sistema", chave, "warning", msg_erro)
                continue

            if not email_valido(email):
                msg_erro = f"E-mail inválido no cadastro: {email}"
                cursor.execute("UPDATE movimentacoes SET alerta_erro = %s WHERE id = %s", (msg_erro, mov_id))
                conn.commit()
                log_acao("verificar_pendencias", "sistema", chave, "error", msg_erro)
                continue

            assunto = f"⚠️ AVISO: Devolução Pendente – Chave/Sala {chave}"
            corpo = f"""
Prezado(a) {usuario},

Consta no Sistema de Controle de Chaves do IFRS – Campus Alvorada que a chave/sala **{chave}** foi retirada em **{formatar_data_br(data_retirada)}** e ainda não foi devolvida.

Até o momento, já se passaram **{horas_atraso:.1f} horas** sem a devolução.

Solicitamos a gentileza de regularizar a situação o mais breve possível, para mantermos o controle e a segurança das instalações.

Atenciosamente,
IFRS – Campus Alvorada
Sistema de Controle de Chaves
"""

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
                    "verificar_pendencias", "sistema", chave, "success",
                    f"E-mail de aviso enviado para {email} | atraso: {horas_atraso:.1f}h"
                )
            except Exception as erro_envio:
                conn.rollback()
                msg_erro = f"Falha ao enviar e-mail: {str(erro_envio)}"
                cursor.execute(
                    "UPDATE movimentacoes SET alerta_erro = %s WHERE id = %s",
                    (msg_erro, mov_id)
                )
                conn.commit()
                log_acao("verificar_pendencias", "sistema", chave, "error", msg_erro)
                continue

        conn.commit()
        return total_pendencias

    except Exception as erro_global:
        conn.rollback()
        log_acao(
            "verificar_pendencias", "sistema", "geral", "error",
            f"Erro geral na verificação: {str(erro_global)}"
        )
        return 0
    finally:
        conn.close()

def ha_chaves_em_atraso():
        """Verifica se existe alguma chave com devolução em atraso"""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT data_retirada
                FROM movimentacoes
                WHERE status = 'indisponivel'
                  AND data_retorno IS NULL
                """
            )
            agora = datetime.now()
            for (data_retirada,) in cursor.fetchall():
                if _esta_em_atraso(data_retirada, agora):
                    return True
            return False
        finally:
            conn.close()