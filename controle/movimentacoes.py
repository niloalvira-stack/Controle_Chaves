# -*- coding: utf-8 -*-
"""
Controle de Chaves — IFRS Campus Alvorada
Módulo: Movimentações
Versão: Final — Layout e Estilos = Segunda Tela
Revisado e Testado
"""

import config
from config import carregar_modo_email, salvar_modo_email
from utils.caminhos import caminho_recurso

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QFormLayout, QLineEdit, QComboBox, QHeaderView,
    QMessageBox, QFileDialog, QDateEdit, QDialogButtonBox, QLabel, QToolButton,
    QAbstractItemView, QListWidget, QListWidgetItem, QRadioButton, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QBrush, QColor

from autenticacao import get_current_user, validar_login
from autenticacao.helpers_autenticacao import get_db_connection
from utils.ui_colors import aplicar_cor_status_item_generico
from utils.validacao import email_valido
from utils.utils import montar_display_sala_por_id, formatar_data_br, _parse_datetime
from utils.utils_log import log_acao
from controle.selecionar_sala_dialog import SelecionarSalaDialog
from utils.email_service import enviar_email

from datetime import datetime, date
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph

ALERTA_HORAS = 12


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _esta_em_atraso(data_retirada, agora=None):
    agora = agora or datetime.now()
    retirada_dt = _parse_datetime(data_retirada)
    if not retirada_dt:
        return False
    if hasattr(retirada_dt, 'tzinfo') and retirada_dt.tzinfo:
        retirada_dt = retirada_dt.replace(tzinfo=None)
    horas_passadas = (agora - retirada_dt).total_seconds() / 3600
    return horas_passadas >= ALERTA_HORAS


def _normalizar_status(status):
    if not status:
        return ""
    s = str(status).strip().lower()
    return {"disponível": "disponivel", "indisponível": "indisponivel"}.get(s, s)


def _normalizar_motivo_emprestimo(motivo):
    if motivo is None:
        return None
    m = str(motivo).strip().lower()
    if m and m not in {"normal", "copia_temporaria", "extravio", "nao_devolvida", "contingencia"}:
        raise ValueError(f"Motivo inválido: {motivo}")
    return m or None


def pode_solicitar_retirada(utilizador_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT vinculo, data_fim_validade, ativo FROM utilizadores WHERE id = %s", (utilizador_id,))
        row = cur.fetchone()
    finally:
        conn.close()
    if not row:
        return False, "Utilizador não encontrado."
    vinculo, data_fim, ativo = row
    if not ativo:
        return False, "Utilizador inativo."
    if str(vinculo or "").strip() == "Servidor(a)" or data_fim is None:
        return True, ""
    return (True, "") if date.today() <= data_fim else (False, f"Validade expirada em {data_fim.strftime('%d/%m/%Y')}")


def obter_chave_fisica_disponivel_por_sala(sala_id, apenas_principal=False):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        sql = "SELECT id, etiqueta, tipo, status FROM chaves_fisicas WHERE sala_id = %s AND ativa = TRUE AND status = 'disponivel'"
        sql += " AND tipo = 'principal' LIMIT 1" if apenas_principal else " ORDER BY CASE tipo WHEN 'principal' THEN 0 WHEN 'reserva' THEN 1 ELSE 2 END, id LIMIT 1"
        cur.execute(sql, [sala_id])
        return cur.fetchone()
    finally:
        conn.close()


def pode_retirar_chave_fisica(chave_fisica_id):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, ativa, status FROM chaves_fisicas WHERE id = %s", (chave_fisica_id,))
        row = cur.fetchone()
    finally:
        conn.close()
    if not row:
        return False, "Chave física não encontrada."
    return (True, "") if row[1] and _normalizar_status(row[2]) == "disponivel" else (False, "Chave não disponível.")


def listar_movimentacoes(data_ini=None, data_fim=None):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        sql = """SELECT m.id, COALESCE(cf.etiqueta, m.chave, ''), m.chave_fisica_id,
            CASE WHEN COALESCE(s.nome, '') <> '' AND COALESCE(s.descricao, '') <> '' THEN s.nome || ' - ' || s.descricao
                 WHEN COALESCE(s.nome, '') <> '' THEN s.nome ELSE COALESCE(s.descricao, '') END,
            COALESCE(u.nome, m.usuario), u.vinculo, m.data_retirada, m.data_retorno, m.status, cf.tipo, m.motivo_emprestimo, s.id, m.alerta_enviado
            FROM movimentacoes m LEFT JOIN utilizadores u ON u.id=m.utilizador_id
            LEFT JOIN salas s ON s.id=m.sala_id LEFT JOIN chaves_fisicas cf ON cf.id=m.chave_fisica_id WHERE 1=1"""
        params = []
        if data_ini is None and data_fim is None:
            sql += " AND m.data_retirada::date = CURRENT_DATE"
        else:
            if data_ini:
                sql += " AND m.data_retirada >= %s"
                params.append(data_ini)
            if data_fim:
                sql += " AND m.data_retirada <= %s"
                params.append(data_fim)
        sql += " ORDER BY m.data_retirada DESC"
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def buscar_movimentacoes_personalizado(chave=None, usuario=None, data_ini=None, data_fim=None, status=None):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        sql = """SELECT m.id, COALESCE(cf.etiqueta, m.chave, ''), m.chave_fisica_id,
            CASE WHEN COALESCE(s.nome, '') <> '' AND COALESCE(s.descricao, '') <> '' THEN s.nome || ' - ' || s.descricao
                 WHEN COALESCE(s.nome, '') <> '' THEN s.nome ELSE COALESCE(s.descricao, '') END,
            COALESCE(u.nome, m.usuario), u.vinculo, m.data_retirada, m.data_retorno, m.status, cf.tipo, m.motivo_emprestimo, s.id, m.alerta_enviado
            FROM movimentacoes m LEFT JOIN utilizadores u ON u.id=m.utilizador_id
            LEFT JOIN salas s ON s.id=m.sala_id LEFT JOIN chaves_fisicas cf ON cf.id=m.chave_fisica_id WHERE 1=1"""
        params = []
        if chave:
            sql += " AND COALESCE(cf.etiqueta, m.chave, '') ILIKE %s"
            params.append(f"%{chave.strip()}%")
        if usuario:
            sql += " AND COALESCE(u.nome, m.usuario) ILIKE %s"
            params.append(f"%{usuario.strip()}%")
        if data_ini:
            sql += " AND m.data_retirada >= %s"
            params.append(data_ini)
        if data_fim:
            sql += " AND m.data_retirada <= %s"
            params.append(data_fim)
        if status and status.lower() not in ["todos", ""]:
            sql += " AND m.status = %s"
            params.append(_normalizar_status(status))
        sql += " ORDER BY m.data_retirada DESC"
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def salas_com_pelo_menos_uma_copia():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT sala_id FROM chaves_fisicas WHERE ativa=TRUE AND tipo='reserva'")
        return {r[0] for r in cur.fetchall()}
    finally:
        conn.close()


def registrar_retirada(sala_id, chave_fisica_id, utilizador_id, email, motivo_emprestimo=None):
    email = (email or "").strip().lower()
    motivo_emprestimo = _normalizar_motivo_emprestimo(motivo_emprestimo)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT nome, ativo FROM utilizadores WHERE id = %s", (utilizador_id,))
        nome_utilizador, ativo = cur.fetchone()
        if not ativo:
            raise ValueError("Utilizador inativo")
        cur.execute("SELECT id, sala_id, etiqueta, ativa, status FROM chaves_fisicas WHERE id = %s FOR UPDATE", (chave_fisica_id,))
        _, sala_id_chave, etiqueta, ativa_ch, status_ch = cur.fetchone()
        if sala_id_chave != sala_id or not ativa_ch or _normalizar_status(status_ch) != "disponivel":
            raise ValueError("Chave indisponível ou não pertence à sala")
        cur.execute(
            "SELECT 1 FROM movimentacoes WHERE chave_fisica_id=%s AND status='indisponivel' AND data_retorno IS NULL LIMIT 1",
            (chave_fisica_id,))
        if cur.fetchone():
            raise ValueError("Chave já retirada")
        chave_display = etiqueta or montar_display_sala_por_id(sala_id)
        hora_atual = datetime.now().replace(tzinfo=None)
        cur.execute("""INSERT INTO movimentacoes (chave,chave_fisica_id,sala_id,utilizador_id,usuario,email,data_retirada,status,alerta_enviado,motivo_emprestimo)
            VALUES (%s,%s,%s,%s,%s,%s,%s,'indisponivel',FALSE,%s)""",
                    (chave_display, chave_fisica_id, sala_id, utilizador_id, nome_utilizador, email, hora_atual, motivo_emprestimo))
        cur.execute("UPDATE salas SET status='indisponivel' WHERE id=%s", (sala_id,))
        cur.execute("UPDATE chaves_fisicas SET status='indisponivel', atualizada_em=%s WHERE id=%s", (hora_atual, chave_fisica_id))
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
        cur = conn.cursor()
        cur.execute("SELECT chave,chave_fisica_id,sala_id,status FROM movimentacoes WHERE id=%s FOR UPDATE", (mov_id,))
        chave, chave_fisica_id, sala_id_db, status_atual = cur.fetchone()
        if _normalizar_status(status_atual) == "disponivel":
            return chave or "", chave_fisica_id, sala_id_db
        sala_id_final = sala_id_db if sala_id is None else sala_id
        hora_atual = datetime.now().replace(tzinfo=None)
        cur.execute("UPDATE movimentacoes SET data_retorno=%s,status='disponivel',alerta_enviado=FALSE WHERE id=%s",
                    (hora_atual, mov_id))
        if sala_id_final:
            cur.execute("UPDATE salas SET status='disponivel' WHERE id=%s", (sala_id_final,))
        if chave_fisica_id:
            cur.execute("UPDATE chaves_fisicas SET status='disponivel',atualizada_em=%s WHERE id=%s",
                        (hora_atual, chave_fisica_id))
        conn.commit()
        return chave or "", chave_fisica_id, sala_id_final
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ha_chaves_em_atraso():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT m.id, m.data_retirada
            FROM movimentacoes m
            WHERE m.status = 'indisponivel'
              AND m.data_retorno IS NULL
            ORDER BY m.data_retirada ASC
        """)
        linhas = cur.fetchall()
        agora = datetime.now()
        contador_atraso = 0
        for mov_id, dt_retirada in linhas:
            dt = _parse_datetime(dt_retirada)
            if not dt:
                continue
            horas_passadas = (agora - dt).total_seconds() / 3600
            if horas_passadas >= ALERTA_HORAS:
                contador_atraso += 1
        return contador_atraso
    finally:
        conn.close()


def verificar_pendencias_e_enviar_emails(modo_manual=False, lista_selecionada=None):
    conn = get_db_connection()
    total_pendencias = 0
    total_enviados = 0
    lista_pendencias = []
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT m.id, m.chave, m.usuario, u.email, m.data_retirada, m.alerta_enviado
            FROM movimentacoes m
            LEFT JOIN utilizadores u ON m.utilizador_id = u.id
            WHERE m.status = 'indisponivel' AND m.data_retorno IS NULL
            ORDER BY m.data_retirada ASC
        """)
        linhas = cur.fetchall()
        agora = datetime.now()
        modo_banco = carregar_modo_email()
        EMAIL_ENVIO_AUTOMATICO = (modo_banco == "automatico")

        for mid, chave, usuario, email, dt_ret, aviso_enviado in linhas:
            if not dt_ret:
                continue
            dt = _parse_datetime(dt_ret)
            if not dt:
                log_acao("verificar_pendencias", "sistema", chave, "erro", f"Data inválida mov={mid}")
                continue
            horas_atraso = (agora - dt).total_seconds() / 3600
            if horas_atraso < ALERTA_HORAS:
                continue
            total_pendencias += 1
            lista_pendencias.append({
                "id": mid,
                "chave": chave,
                "usuario": usuario,
                "email": email or "— Sem e-mail —",
                "dt_retirada": dt,
                "horas_atraso": round(horas_atraso, 1),
                "ja_enviado": aviso_enviado
            })
            if modo_manual:
                if lista_selecionada and mid in lista_selecionada and not aviso_enviado:
                    if _enviar_e_atualizar(mid, chave, usuario, email, dt, cur, conn):
                        total_enviados += 1
                continue
            if EMAIL_ENVIO_AUTOMATICO and not aviso_enviado:
                if _enviar_e_atualizar(mid, chave, usuario, email, dt, cur, conn):
                    total_enviados += 1
        conn.commit()
    except Exception as e:
        conn.rollback()
        log_acao("verificar_pendencias", "sistema", "-", "erro", f"Falha geral: {e}")
    finally:
        conn.close()
    return total_pendencias, total_enviados, lista_pendencias


def _enviar_e_atualizar(mid, chave, usuario, email, dt, cur, conn):
    if not email:
        cur.execute("UPDATE movimentacoes SET alerta_erro = %s WHERE id=%s",
                    ("Sem e-mail cadastrado", mid))
        return False
    if not email_valido(email):
        cur.execute("UPDATE movimentacoes SET alerta_erro = %s WHERE id=%s",
                    (f"E-mail inválido: {email}", mid))
        return False

    ass = f"📌 Lembrando: Devolução da Chave {chave}"
    corpo = f"""<html><body style="font-family:Arial,sans-serif;font-size:14px;line-height:1.6;">
<h2 style="color:#2c5aa0;">Lembrando da Devolução</h2>
<p>Olá, <strong>{usuario}</strong>!</p>
<p>Passando para lembrar-lhe de que a chave <strong>{chave}</strong> ainda não foi devolvida. Ela foi retirada em <strong>{formatar_data_br(dt)}</strong>.</p>
<p>Se possível, pedimos que providencie a devolução o quanto antes, para que outros também possam utilizar.</p>
<p style="color:#555; font-size:13px; margin-top:20px;">
<strong>📌 Se já devolveu a chave recentemente, por favor desconsidere este aviso — o sistema ainda não registrou a recente, por favor desconsidere este aviso — o sistema ainda não registrou a devolução.</strong>
</p>
<p style="color:#777; font-size:12px; margin-top:10px;">
⚠️ Este é um e-mail automático do sistema, por favor <strong>não responda</strong> a esta mensagem.
</p>
<p style="margin-top: 30px;">Agradecemos a sua colaboração! 😊</p>
<p>Atenciosamente,<br>Equipe de Controle de Chaves<br>IFRS — Campus Alvorada</p>
</body></html>"""

    resultado = enviar_email(email, ass, corpo)
    if isinstance(resultado, bool):
        ok = resultado
        mensagem = "E-mail enviado com sucesso" if ok else "Falha desconhecida"
    else:
        ok, mensagem = resultado

    if ok:
        cur.execute("""
            UPDATE movimentacoes
            SET alerta_enviado = TRUE, alerta_enviado_em = NOW(), alerta_erro = NULL
            WHERE id = %s
        """, (mid,))
        log_acao("verificar_pendencias", "sistema", chave, "sucesso", f"E-mail enviado para {email}")
        return True
    else:
        cur.execute("UPDATE movimentacoes SET alerta_erro = %s WHERE id = %s", (mensagem, mid))
        log_acao("verificar_pendencias", "sistema", chave, "erro", f"Falha: {mensagem}")
        return False


# ============================================================
# DIÁLOGOS
# ============================================================

class TelaEnvioManualEmails(QDialog):
    def __init__(self, lista_pendencias, parent=None):
        super().__init__(parent)
        self.lista_pendencias = lista_pendencias
        self.selecionados = []
        self.setWindowTitle("Envio Manual de Avisos de Atraso")
        self.resize(900, 500)
        self._construir_interface()

    def _construir_interface(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "📋 Selecione abaixo os avisos que deseja enviar por e-mail.\n"
            "Avisos já enviados anteriormente não serão reenviados."
        ))

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels(
            ["", "Chave", "Responsável", "E-mail", "Horas Atraso", "Status"]
        )
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.setRowCount(len(self.lista_pendencias))

        for linha, item in enumerate(self.lista_pendencias):
            chk = QCheckBox()
            chk.setEnabled(not item["ja_enviado"])
            if not item["ja_enviado"]:
                chk.stateChanged.connect(lambda est, mid=item["id"]: self._marcar(mid, est))
            self.tabela.setCellWidget(linha, 0, chk)
            self.tabela.setItem(linha, 1, QTableWidgetItem(item["chave"]))
            self.tabela.setItem(linha, 2, QTableWidgetItem(item["usuario"]))
            self.tabela.setItem(linha, 3, QTableWidgetItem(item["email"]))
            self.tabela.setItem(linha, 4, QTableWidgetItem(f"{item['horas_atraso']}h"))
            status = "✅ Já enviado" if item["ja_enviado"] else "⏳ Pendente"
            self.tabela.setItem(linha, 5, QTableWidgetItem(status))

        layout.addWidget(self.tabela)

        botoes = QHBoxLayout()
        self.btn_todos = QPushButton("Selecionar Todos Pendentes")
        self.btn_todos.clicked.connect(self._selecionar_todos)
        self.btn_enviar = QPushButton("📧 Enviar Avisos Selecionados")
        self.btn_enviar.setStyleSheet("background-color: #28a745; color: white; padding: 6px; font-weight:bold;")
        self.btn_enviar.clicked.connect(self._enviar_selecionados)
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)

        botoes.addWidget(self.btn_todos)
        botoes.addStretch()
        botoes.addWidget(self.btn_cancelar)
        botoes.addWidget(self.btn_enviar)
        layout.addLayout(botoes)

    def _marcar(self, mid, estado):
        if estado == 2:
            if mid not in self.selecionados:
                self.selecionados.append(mid)
        else:
            if mid in self.selecionados:
                self.selecionados.remove(mid)

    def _selecionar_todos(self):
        for linha in range(self.tabela.rowCount()):
            chk = self.tabela.cellWidget(linha, 0)
            if chk and chk.isEnabled():
                chk.setChecked(True)

    def _enviar_selecionados(self):
        if not self.selecionados:
            QMessageBox.information(self, "Aviso", "Selecione pelo menos um aviso para enviar.")
            return
        total, enviados, _ = verificar_pendencias_e_enviar_emails(
            modo_manual=True, lista_selecionada=self.selecionados
        )
        QMessageBox.information(self, "Concluído",
                                f"✅ Processo finalizado!\n\n"
                                f"Pendências encontradas: {total}\n"
                                f"Avisos enviados agora: {enviados}"
                                )
        self.accept()


class FiltroMovimentacaoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filtrar Movimentações")
        lyt = QFormLayout(self)
        self.data_inicio = QDateEdit(QDate.currentDate())
        self.data_inicio.setDisplayFormat("dd/MM/yyyy")
        self.data_inicio.setCalendarPopup(True)
        self.data_fim = QDateEdit(QDate.currentDate())
        self.data_fim.setDisplayFormat("dd/MM/yyyy")
        self.data_fim.setCalendarPopup(True)
        self.input_usuario = QLineEdit()
        self.combo_status = QComboBox()
        self.combo_status.addItems(["Todos", "disponível", "indisponível"])
        lyt.addRow("Data Início:", self.data_inicio)
        lyt.addRow("Data Fim:", self.data_fim)
        lyt.addRow("Utilizador:", self.input_usuario)
        lyt.addRow("Status:", self.combo_status)
        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn.accepted.connect(self.accept)
        btn.rejected.connect(self.reject)
        lyt.addWidget(btn)

    def get_filters(self):
        ini = self.data_inicio.date().toString("yyyy-MM-dd") + " 00:00:00"
        fim = self.data_fim.date().toString("yyyy-MM-dd") + " 23:59:59"
        st = None if self.combo_status.currentText() == "Todos" else _normalizar_status(self.combo_status.currentText())
        return {
            "data_ini": ini,
            "data_fim": fim,
            "usuario": self.input_usuario.text().strip().lower() or None,
            "status": st
        }


# ============================================================
# ✅ CLASSE PRINCIPAL — LAYOUT IGUAL À SEGUNDA TELA
# ============================================================

class MovimentacoesTab(QWidget):
    def __init__(self, dash_main_ref=None):
        super().__init__()
        self.dash_main_ref = dash_main_ref
        self.sala_id_atual = None
        self.filtro_atual = None
        self.chave_fisica_id_atual = None
        self._em_operacao = False
        self.filtro_apenas_copias = False

        # Verificação de admin
        self.eh_admin = False
        self.utilizador_atual = get_current_user()

        if self.utilizador_atual:
            if hasattr(self.utilizador_atual, "is_admin"):
                self.eh_admin = bool(self.utilizador_atual.is_admin)
            elif isinstance(self.utilizador_atual, dict):
                self.eh_admin = bool(self.utilizador_atual.get("is_admin", False))
            if not self.eh_admin and self.dash_main_ref and hasattr(self.dash_main_ref, 'eh_admin'):
                self.eh_admin = self.dash_main_ref.eh_admin

        print(f"🔍 MOV — eh_admin = {self.eh_admin} | tipo = {type(self.utilizador_atual).__name__}")

        # Estilo global — igual à segunda tela
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: Arial, sans-serif;
                font-size: 13px;
                color: #212529;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                gridline-color: #dee2e6;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                color: #495057;
                font-weight: bold;
                padding: 10px;
                border: 1px solid #dee2e6;
            }
            QPushButton {
                font-size: 13px;
                font-weight: bold;
                border-radius: 4px;
            }
            QLineEdit, QComboBox {
                padding: 5px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                min-height: 22px;
            }
        """)

        self.label_atraso = None
        self.init_ui()

        try:
            self.carregar_movimentacoes()
        except Exception as e:
            print(f"Erro ao carregar: {e}")

        # Atualização automática da tabela
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.carregar_movimentacoes)
        self.timer.start(5000)

        # Sincronização do modo de envio com o banco
        self.timer_sincronia_modo = QTimer(self)
        self.timer_sincronia_modo.timeout.connect(self._atualizar_modo_da_interface)
        self.timer_sincronia_modo.start(8000)

    def _notificar_operacao(self, msg):
        if self.dash_main_ref and hasattr(self.dash_main_ref, "show_operation_done"):
            self.dash_main_ref.show_operation_done(msg)

    def _preservar_mov_id_selecionado(self):
        sel = self.table.selectionModel().selectedRows()
        return self.table.item(sel[0].row(), 0).text().strip() if sel else None

    def _restaurar_selecao_por_mov_id(self, mid):
        if not mid:
            return
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0) and self.table.item(r, 0).text().strip() == str(mid):
                self.table.selectRow(r)
                break

    def _atualizar_contagem_pendencias(self):
        qtd = ha_chaves_em_atraso()
        if qtd > 0 and self.label_atraso:
            self.label_atraso.setText(f"⚠️ {qtd} chave(s) em ATRASO!")
            self.label_atraso.setStyleSheet("color: #dc3545; font-weight: bold; font-size: 11pt;")
            self.label_atraso.setVisible(True)
        elif self.label_atraso:
            self.label_atraso.setVisible(False)

    def _atualizar_modo_da_interface(self):
        """Atualiza os rádios se mudou em outro cliente"""
        modo_banco = carregar_modo_email()
        self.modo_auto.blockSignals(True)
        self.modo_manual.blockSignals(True)
        if modo_banco == "automatico":
            if not self.modo_auto.isChecked():
                self.modo_auto.setChecked(True)
        else:
            if not self.modo_manual.isChecked():
                self.modo_manual.setChecked(True)
        self.modo_auto.blockSignals(False)
        self.modo_manual.blockSignals(False)

    def _restaurar_modo(self, modo):
        self.modo_auto.blockSignals(True)
        self.modo_manual.blockSignals(True)
        self.modo_auto.setChecked(modo == "automatico")
        self.modo_manual.setChecked(modo != "automatico")
        self.modo_auto.blockSignals(False)
        self.modo_manual.blockSignals(False)

    def _ao_mudar_modo_com_senha(self):
        """Só admin pode alterar — com confirmação"""
        if not self.eh_admin:
            QMessageBox.warning(self, "Acesso Negado", "Apenas administradores podem alterar o modo de envio de e-mails.")
            self._restaurar_modo(carregar_modo_email())
            return

        modo_original = carregar_modo_email()

        dlg = QDialog(self)
        dlg.setWindowTitle("🔒 Confirmação de Alteração")
        dlg.setMinimumWidth(420)
        layout = QVBoxLayout(dlg)

        nome_user = getattr(self.utilizador_atual, 'nome', None) or self.utilizador_atual.get('nome', 'Usuário')
        login_user = getattr(self.utilizador_atual, 'login', None) or self.utilizador_atual.get('login', '')

        layout.addWidget(QLabel(
            f"<b>Confirmação necessária</b><br><br>"
            f"Você está prestes a alterar o <b>modo de envio de e-mails</b>.<br><br>"
            f"👤 Usuário: <b>{nome_user}</b><br>"
            f"🔑 Login: <b>{login_user}</b><br><br>"
            f"Deseja confirmar esta alteração?"
        ))

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes |
            QDialogButtonBox.StandardButton.Cancel
        )
        botoes.button(QDialogButtonBox.StandardButton.Yes).setText("✅ Confirmar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("❌ Cancelar")
        layout.addWidget(botoes)
        botoes.accepted.connect(dlg.accept)
        botoes.rejected.connect(dlg.reject)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            self._restaurar_modo(modo_original)
            return

        if self.modo_auto.isChecked():
            salvar_modo_email("automatico")
            novo_modo = "Automático"
        else:
            salvar_modo_email("manual")
            novo_modo = "Manual"

        QMessageBox.information(
            self, "✅ Alteração Concluída",
            f"O modo de envio foi alterado para <b>{novo_modo}</b> com sucesso!"
        )
        log_acao("configuracao", login_user, "-", "alteracao", f"Modo envio e-mail → {novo_modo}")

    def acao_verificar_pendencias(self):
        modo_atual = carregar_modo_email()
        if modo_atual == "automatico":
            verificar_pendencias_e_enviar_emails()
            QMessageBox.information(self, "✅ Verificação Concluída",
                                    "Verificação concluída.\nOs e-mails foram enviados automaticamente.")
        else:
            self.abrir_janela_envio_manual()

    def abrir_janela_envio_manual(self):
        total, enviados, lista_pendencias = verificar_pendencias_e_enviar_emails(modo_manual=True)
        if not lista_pendencias:
            QMessageBox.information(self, "✅ Nenhuma Pendência",
                                    "Não há chaves em atraso para notificar.")
            return
        dlg = TelaEnvioManualEmails(lista_pendencias, self)
        dlg.exec()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Título
        layout.addWidget(QLabel("<h2>Movimentações de Chaves/Salas</h2>"))

        # Aviso de atraso
        self.label_atraso = QLabel("")
        self.label_atraso.setVisible(False)
        layout.addWidget(self.label_atraso)

        # ─── LINHA DE SELEÇÃO DE SALA E AÇÕES ───
        linha_sala = QHBoxLayout()
        linha_sala.setSpacing(10)

        linha_sala.addWidget(QLabel("Sala:"))
        self.label_sala_selecionada = QLineEdit()
        self.label_sala_selecionada.setReadOnly(True)
        self.label_sala_selecionada.setPlaceholderText("Nenhuma sala selecionada")
        linha_sala.addWidget(self.label_sala_selecionada, stretch=1)

        self.btn_selecionar_sala = QPushButton("Selecionar sala...")
        self.btn_selecionar_sala.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #ccc;
                padding: 6px 12px;
                border-radius: 4px;
                min-height: 22px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        self.btn_selecionar_sala.clicked.connect(self.abrir_dialogo_salas)
        linha_sala.addWidget(self.btn_selecionar_sala)

        self.combo_utilizador = QComboBox()
        self.combo_utilizador.setPlaceholderText("Selecione...")
        linha_sala.addWidget(self.combo_utilizador, stretch=1)

        self.btn_utilizador = QPushButton("+ Utilizador")
        self.btn_utilizador.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                padding: 6px 12px;
                border-radius: 4px;
                min-height: 22px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        self.btn_utilizador.clicked.connect(self.cadastrar_utilizador_rapido)
        linha_sala.addWidget(self.btn_utilizador)

        linha_sala.addWidget(QLabel("Motivo:"))
        self.combo_motivo = QComboBox()
        self.combo_motivo.addItems([
            "normal",
            "copia_temporaria",
            "extravio",
            "nao_devolvida",
            "contingencia"
        ])
        self.combo_motivo.setCurrentText("normal")
        linha_sala.addWidget(self.combo_motivo)

        self.btn_retirada = QPushButton("Registrar Retirada")
        self.btn_retirada.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 6px 14px;
                border-radius: 4px;
                min-height: 22px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.btn_retirada.clicked.connect(self.adicionar_movimentacao)
        linha_sala.addWidget(self.btn_retirada)

        self.btn_devolucao = QPushButton("Registrar Devolução")
        self.btn_devolucao.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 6px 14px;
                border-radius: 4px;
                min-height: 22px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.btn_devolucao.clicked.connect(self.devolver_selecionada)
        linha_sala.addWidget(self.btn_devolucao)

        layout.addLayout(linha_sala)

        # ─── LINHA DE FILTROS E MODO DE ENVIO ───
        linha_filtros = QHBoxLayout()
        linha_filtros.setSpacing(10)

        self.btn_filtrar = QPushButton("🔍 Filtrar")
        self.btn_filtrar.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                padding: 6px 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        self.btn_filtrar.clicked.connect(self.abrir_filtro_modal)
        linha_filtros.addWidget(self.btn_filtrar)

        self.btn_verificar = QPushButton("Verificar pendências")
        self.btn_verificar.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 6px 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.btn_verificar.clicked.connect(self.acao_verificar_pendencias)
        linha_filtros.addWidget(self.btn_verificar)

        linha_filtros.addWidget(QLabel("Modo de Envio:"))

        self.modo_auto = QRadioButton("Automático")
        self.modo_manual = QRadioButton("Manual")

        modo_atual = carregar_modo_email()
        if modo_atual == "automatico":
            self.modo_auto.setChecked(True)
        else:
            self.modo_manual.setChecked(True)

        self.modo_auto.toggled.connect(self._ao_mudar_modo_com_senha)

        linha_filtros.addWidget(self.modo_auto)
        linha_filtros.addWidget(self.modo_manual)

        linha_filtros.addStretch()

        self.btn_csv = QPushButton("Exportar CSV")
        self.btn_csv.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 6px 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.btn_csv.clicked.connect(self.exportar_csv)
        linha_filtros.addWidget(self.btn_csv)

        self.btn_pdf = QPushButton("Exportar PDF")
        self.btn_pdf.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 6px 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.btn_pdf.clicked.connect(self.exportar_pdf)
        linha_filtros.addWidget(self.btn_pdf)

        layout.addLayout(linha_filtros)

        # ─── TABELA PRINCIPAL ───
        self.table = QTableWidget()

        colunas = [
            "Chave",
            "Chave física ID",
            "Descrição sala",
            "Utilizador",
            "Vínculo",
            "Retirada",
            "Devolução",
            "Status",
            "Tipo",
            "Motivo",
            "Aviso"
        ]

        self.table.setColumnCount(len(colunas))
        self.table.setHorizontalHeaderLabels(colunas)

        cabecalho = self.table.horizontalHeader()
        for i in range(len(colunas)):
            cabecalho.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table)

        self._atualizar_contagem_pendencias()

    def abrir_dialogo_salas(self):
        dlg = SelecionarSalaDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.sala_id_atual = getattr(dlg, 'sala_id_selecionada', None) or getattr(dlg, 'sala_id', None)
            display = getattr(dlg, 'sala_display_selecionada', None) or getattr(dlg, 'sala_nome_selecionada', "")
            self.label_sala_selecionada.setText(display or "")
            self.carregar_utilizadores_por_sala()
            self.carregar_movimentacoes()

    def carregar_utilizadores_por_sala(self):
        self.combo_utilizador.clear()
        if not self.sala_id_atual:
            return
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT u.id, u.nome
                FROM utilizadores u
                LEFT JOIN movimentacoes m ON m.utilizador_id = u.id
                WHERE u.ativo = TRUE
                   OR m.sala_id = %s
                ORDER BY u.nome
            """, (self.sala_id_atual,))
            for uid, nome in cur.fetchall():
                self.combo_utilizador.addItem(nome, uid)
        finally:
            conn.close()

    def cadastrar_utilizador_rapido(self):
        """Cadastro Rápido — Lógica IDÊNTICA à aba Utilizadores"""
        from email_validator import validate_email, EmailNotValidError
        from utils.button_style import aplicar_estilo_botao_padrao
        from contextlib import closing

        dlg = QDialog(self)
        dlg.setWindowTitle("Utilizador")
        dlg.setMinimumWidth(420)

        layout = QFormLayout(dlg)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # === CAMPOS IGUAIS ===
        edit_nome = QLineEdit()
        edit_email = QLineEdit()

        combo_vinculo = QComboBox()
        combo_vinculo.addItem("Escolher vínculo...")
        combo_vinculo.addItems([
            "Servidor(a)",
            "Aluno(a)",
            "Bolsista",
            "Monitor(a)",
            "Estagiário(a)",
            "Externo(a)",
        ])
        combo_vinculo.setCurrentIndex(0)

        combo_ativo = QComboBox()
        combo_ativo.addItems(["Sim", "Não"])
        combo_ativo.setCurrentIndex(0)

        date_fim = QDateEdit()
        date_fim.setCalendarPopup(True)
        date_fim.setDisplayFormat("dd/MM/yyyy")
        date_fim.setEnabled(False)  # Inicia bloqueado

        layout.addRow("Nome:", edit_nome)
        layout.addRow("E-mail:", edit_email)
        layout.addRow("Vínculo *:", combo_vinculo)
        layout.addRow("Ativo:", combo_ativo)
        layout.addRow("Válido até:", date_fim)

        # === BOTÕES — MESMO ESTILO ===
        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btn_salvar = botoes.button(QDialogButtonBox.StandardButton.Save)
        btn_cancelar = botoes.button(QDialogButtonBox.StandardButton.Cancel)

        aplicar_estilo_botao_padrao(btn_salvar, "#0d6efd", "#ffffff")
        aplicar_estilo_botao_padrao(btn_cancelar, "#6c757d", "#ffffff")

        layout.addRow(botoes)

        # === LÓGICA DE CÁLCULO DE DATA — EXATAMENTE IGUAL ===
        def _atualizar_data_por_vinculo(vinculo):
            hoje = QDate.currentDate()
            if vinculo == "Escolher vínculo...":
                date_fim.clear()
                date_fim.setEnabled(False)
                return
            if vinculo == "Servidor(a)":
                date_fim.clear()
                date_fim.setEnabled(False)
            elif vinculo == "Aluno(a)":
                date_fim.setDate(hoje.addDays(7))
                date_fim.setEnabled(True)
            elif vinculo in ("Bolsista", "Estagiário(a)", "Monitor(a)"):
                date_fim.setDate(QDate(hoje.year(), 12, 31))
                date_fim.setEnabled(True)
            elif vinculo in ("Externo", "Externo(a)"):
                date_fim.setDate(hoje.addDays(90))
                date_fim.setEnabled(True)
            else:
                date_fim.setEnabled(True)

        combo_vinculo.currentTextChanged.connect(_atualizar_data_por_vinculo)

        # === VALIDAÇÃO DE E-MAIL — MESMA FUNÇÃO ===
        def _validar_email(email):
            email = (email or "").strip()
            if not email:
                return True, ""  # E-mail opcional no cadastro rápido
            try:
                info = validate_email(email, check_deliverability=False)
                return True, info.normalized.lower()
            except EmailNotValidError as e:
                QMessageBox.warning(dlg, "E-mail inválido", str(e))
                return False, email

        # === SALVAR ===
        def _salvar():
            nome = edit_nome.text().strip()
            email_entrada = edit_email.text().strip()
            vinculo = combo_vinculo.currentText()
            ativo = (combo_ativo.currentText() == "Sim")
            hoje = QDate.currentDate()

            # Validações iguais
            if not nome:
                QMessageBox.warning(dlg, "Dados incompletos", "Nome é obrigatório!")
                return
            if vinculo == "Escolher vínculo...":
                QMessageBox.warning(dlg, "Seleção obrigatória", "Escolha um vínculo!")
                return

            # Processa data
            if vinculo == "Servidor(a)":
                data_fim_validade = None
            elif vinculo == "Aluno(a)":
                data_fim_validade = hoje.addDays(7).toPyDate()
            elif vinculo in ("Bolsista", "Estagiário(a)", "Monitor(a)"):
                data_fim_validade = QDate(hoje.year(), 12, 31).toPyDate()
            elif vinculo in ("Externo", "Externo(a)"):
                data_fim_validade = hoje.addDays(90).toPyDate()
            else:
                data_fim_validade = date_fim.date().toPyDate() if date_fim.date().isValid() else None

            # Valida e-mail
            ok_email, email_normalizado = _validar_email(email_entrada)
            if not ok_email:
                return

            # Inserção no banco
            try:
                with closing(get_db_connection()) as conn, conn.cursor() as cur:
                    # Verifica duplicidade
                    cur.execute("SELECT id FROM utilizadores WHERE nome = %s", (nome,))
                    if cur.fetchone():
                        QMessageBox.warning(dlg, "Aviso", "Já existe um utilizador com este nome!")
                        return
                    if email_normalizado:
                        cur.execute("SELECT id FROM utilizadores WHERE email = %s", (email_normalizado,))
                        if cur.fetchone():
                            QMessageBox.warning(dlg, "Aviso", "Este e-mail já está cadastrado!")
                            return

                    cur.execute("""
                        INSERT INTO utilizadores (nome, email, vinculo, ativo, data_fim_validade)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (nome, email_normalizado or None, vinculo, ativo, data_fim_validade))
                    novo_id = cur.fetchone()[0]
                    conn.commit()

                QMessageBox.information(
                    dlg, "✅ Cadastrado",
                    f"Utilizador cadastrado!\n\n"
                    f"Nome: {nome}\n"
                    f"Vínculo: {vinculo}\n"
                    f"Válido até: {data_fim_validade.strftime('%d/%m/%Y') if data_fim_validade else 'Sem vencimento'}\n"
                    f"ID: {novo_id}"
                )

                # Recarrega lista
                self.carregar_utilizadores_por_sala()
                # Seleciona o novo
                idx = self.combo_utilizador.findText(nome)
                if idx >= 0:
                    self.combo_utilizador.setCurrentIndex(idx)

                dlg.accept()

            except Exception as e:
                QMessageBox.critical(dlg, "Erro", f"Falha:\n{str(e)}")

        botoes.accepted.connect(_salvar)
        botoes.rejected.connect(dlg.reject)

        dlg.exec()

    def carregar_movimentacoes(self):
        if self._em_operacao:
            return
        self._em_operacao = True
        try:
            sel_id = self._preservar_mov_id_selecionado()
            self.table.setRowCount(0)

            if self.filtro_atual:
                dados = buscar_movimentacoes_personalizado(
                    usuario=self.filtro_atual["usuario"],
                    data_ini=self.filtro_atual["data_ini"],
                    data_fim=self.filtro_atual["data_fim"],
                    status=self.filtro_atual["status"]
                )
            else:
                dados = listar_movimentacoes()

            agora = datetime.now()
            for linha, reg in enumerate(dados):
                self.table.insertRow(linha)
                chave = reg[1] or ""
                chave_fisica_id = str(reg[2]) if reg[2] else ""
                sala = reg[3] or ""
                resp = reg[4] or ""
                vinc = reg[5] or ""
                dt_ret = formatar_data_br(reg[6]) if reg[6] else ""
                dt_dev = formatar_data_br(reg[7]) if reg[7] else ""
                status = reg[8] or ""
                tipo = reg[9] or ""
                motivo = reg[10] or ""
                alerta_enviado = reg[12] if len(reg) > 12 else False

                em_atraso = _esta_em_atraso(reg[6], agora) and reg[7] is None

                itens = [
                    QTableWidgetItem(chave),
                    QTableWidgetItem(chave_fisica_id),
                    QTableWidgetItem(sala),
                    QTableWidgetItem(resp),
                    QTableWidgetItem(vinc),
                    QTableWidgetItem(dt_ret),
                    QTableWidgetItem(dt_dev),
                    QTableWidgetItem(status),
                    QTableWidgetItem(tipo),
                    QTableWidgetItem(motivo),
                    QTableWidgetItem("✅" if alerta_enviado else "❌")
                ]

                for c, item in enumerate(itens):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    # Cores de status
                    if c == 7:
                        if _normalizar_status(status) == "disponivel":
                            item.setBackground(QBrush(QColor(212, 237, 218)))
                        elif _normalizar_status(status) == "indisponivel":
                            item.setBackground(QBrush(QColor(255, 243, 205)))

                    # Cor de atraso
                    if em_atraso and c in (5, 6, 10):
                        item.setBackground(QBrush(QColor(255, 205, 205)))

                    self.table.setItem(linha, c, item)

            self._restaurar_selecao_por_mov_id(sel_id)
            self._atualizar_contagem_pendencias()
        finally:
            self._em_operacao = False

    def abrir_filtro_modal(self):
        dlg = FiltroMovimentacaoDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.filtro_atual = dlg.get_filters()
            self.carregar_movimentacoes()

    def adicionar_movimentacao(self):
        if not self.sala_id_atual:
            QMessageBox.warning(self, "Aviso", "Selecione uma sala primeiro.")
            return
        utilizador_id = self.combo_utilizador.currentData()
        if not utilizador_id:
            QMessageBox.warning(self, "Aviso", "Selecione um utilizador.")
            return
        motivo = self.combo_motivo.currentText()
        try:
            chave_fisica = obter_chave_fisica_disponivel_por_sala(self.sala_id_atual)
            if not chave_fisica:
                QMessageBox.warning(self, "Indisponível", "Nenhuma chave disponível para esta sala.")
                return
            chave_fisica_id = chave_fisica[0]
            registrar_retirada(self.sala_id_atual, chave_fisica_id, utilizador_id, "", motivo)
            QMessageBox.information(self, "✅ Sucesso", "Retirada registrada!")
            self.carregar_movimentacoes()
            self._notificar_operacao("Retirada registrada com sucesso")
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def devolver_selecionada(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.warning(self, "Aviso", "Selecione uma movimentação.")
            return
        # Pega o ID real do banco
        linha = sel[0].row()
        # Precisamos do ID que está no banco — ajustar conforme índice real
        # Aqui assumimos que a consulta retorna ID como primeiro campo
        mov_id = listar_movimentacoes()[linha][0]
        try:
            registrar_devolucao(mov_id)
            QMessageBox.information(self, "✅ Sucesso", "Devolução registrada!")
            self.carregar_movimentacoes()
            self._notificar_operacao("Devolução registrada com sucesso")
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def exportar_csv(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "Arquivo CSV (*.csv)")
        if not caminho:
            return
        try:
            with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow([
                    "Chave", "Chave Física ID", "Sala", "Responsável", "Vínculo",
                    "Data Retirada", "Data Devolução", "Status", "Tipo", "Motivo", "Aviso"
                ])
                for r in range(self.table.rowCount()):
                    w.writerow([
                        self.table.item(r, c).text() if self.table.item(r, c) else ""
                        for c in range(self.table.columnCount())
                    ])
            QMessageBox.information(self, "✅ Exportado", f"Arquivo salvo:\n{caminho}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def exportar_pdf(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "", "Documento PDF (*.pdf)")
        if not caminho:
            return
        try:
            doc = SimpleDocTemplate(caminho, pagesize=landscape(A4))
            estilo = getSampleStyleSheet()
            estilo_normal = ParagraphStyle(name="Normal", fontSize=9, leading=11)
            dados = [
                ["Chave", "Sala", "Responsável", "Vínculo", "Retirada", "Devolução", "Status", "Aviso"]
            ]
            for r in range(self.table.rowCount()):
                dados.append([
                    Paragraph(self.table.item(r, 0).text() or "", estilo_normal),
                    Paragraph(self.table.item(r, 2).text() or "", estilo_normal),
                    Paragraph(self.table.item(r, 3).text() or "", estilo_normal),
                    Paragraph(self.table.item(r, 4).text() or "", estilo_normal),
                    Paragraph(self.table.item(r, 5).text() or "", estilo_normal),
                    Paragraph(self.table.item(r, 6).text() or "", estilo_normal),
                    Paragraph(self.table.item(r, 7).text() or "", estilo_normal),
                    Paragraph(self.table.item(r, 10).text() or "", estilo_normal)
                ])
                tabela = Table(dados, colWidths=[80, 130, 110, 70, 90, 90, 80, 60])
                tabela.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]))
            doc.build([
                Spacer(1, 20),
                Paragraph("Relatório de Movimentações de Chaves", estilo["Title"]),
                Spacer(1, 15),
                Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", estilo["Normal"]),
                Spacer(1, 15),
                tabela
            ])
            QMessageBox.information(self, "✅ Exportado", f"PDF salvo com sucesso!\n\n{caminho}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao gerar PDF:\n{str(e)}")