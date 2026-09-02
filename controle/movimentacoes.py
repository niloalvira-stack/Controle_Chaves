from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QFormLayout, QLineEdit, QComboBox, QHeaderView,
    QMessageBox, QFileDialog, QDateEdit, QDialogButtonBox, QLabel, QToolButton,
    QAbstractItemView
)
from PyQt6.QtGui import QBrush, QColor, QImage, QPixmap
from PyQt6.QtCore import Qt, QDate, QTimer
from datetime import datetime, date
import csv
import qrcode
import base64
from io import BytesIO
import cv2
from pyzbar.pyzbar import decode

# ✅ Imports corrigidos
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Image, Paragraph

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

# ═══════ QR Code e Etiquetas ═══════
def gerar_qrcode_dados(chave_id, etiqueta, sala_nome, tipo_chave):
    return f"CHAVE|{chave_id}|{etiqueta}|{sala_nome}|{tipo_chave}"

def gerar_qrcode_imagem(chave_id, etiqueta, sala_nome, tipo_chave):
    dados = gerar_qrcode_dados(chave_id, etiqueta, sala_nome, tipo_chave)
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=6, border=2)
    qr.add_data(dados)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8"), dados

def ler_qrcode_texto(texto_lido):
    if not texto_lido or not str(texto_lido).startswith("CHAVE|"):
        return None
    partes = str(texto_lido).split("|")
    if len(partes) >= 5:
        return {"chave_id": int(partes[1]), "etiqueta": partes[2], "sala_nome": partes[3], "tipo_chave": partes[4]}
    return None

def registrar_devolucao_por_qrcode(texto_lido_qrcode):
    dados = ler_qrcode_texto(texto_lido_qrcode)
    if not dados:
        return False, "QR Code inválido ou não reconhecido"
    chave_id = dados["chave_id"]
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM movimentacoes WHERE chave_fisica_id = %s AND status = 'indisponivel' AND data_retorno IS NULL ORDER BY data_retirada DESC LIMIT 1", (chave_id,))
        mov = cur.fetchone()
        if not mov:
            return False, f"A chave {dados['etiqueta']} não está retirada."
        chave_dev, chave_fis, sala_id = registrar_devolucao(mov[0])
        return True, f"✅ Devolvida: {chave_dev}"
    except Exception as e:
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()

def gerar_etiquetas_pdf(caminho_arquivo, lista_chaves):
    from reportlab.lib.units import cm
    doc = SimpleDocTemplate(caminho_arquivo, pagesize=A4, leftMargin=1*cm, rightMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    estilo = getSampleStyleSheet()["Normal"]
    estilo.fontSize = 10
    estilo.leading = 12
    elementos = []
    for ch in lista_chaves:
        b64, _ = gerar_qrcode_imagem(ch["id"], ch["etiqueta"], ch["sala_nome"], ch["tipo"])
        img_qr = Image(BytesIO(base64.b64decode(b64)), width=3.5*cm, height=3.5*cm)
        elementos.extend([img_qr, Paragraph(f"<b>{ch['etiqueta']}</b>", estilo),
                         Paragraph(f"Sala: {ch['sala_nome']}", estilo),
                         Paragraph(f"Tipo: {ch['tipo'].upper()}", estilo), Spacer(1, 0.6*cm)])
    doc.build(elementos)
    return caminho_arquivo

## ═══════ LEITURA COM LEITOR DE QR CODE (USB) — preservada para uso futuro ═══════
class LeituraQRDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📷 Ler QR Code — Devolução")
        self.setMinimumSize(500, 220)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("<h3>📷 Aproxime o QR Code do leitor</h3>"))
        layout.addWidget(QLabel("Aponte o leitor para a etiqueta da chave.<br>O código será lido automaticamente."))

        self.campo_codigo = QLineEdit()
        self.campo_codigo.setPlaceholderText("Aguardando leitura do leitor...")
        self.campo_codigo.setStyleSheet("font-size: 14px; padding: 8px; border: 2px solid #ccc; border-radius: 4px;")
        self.campo_codigo.textChanged.connect(self.quando_mudar_texto)
        layout.addWidget(self.campo_codigo)

        self.label_status = QLabel("✅ Pronto para ler!")
        self.label_status.setStyleSheet("color: green; font-weight: bold; margin-top: 5px;")
        layout.addWidget(self.label_status)

        linha_botoes = QHBoxLayout()
        self.btn_limpar = QPushButton("🔄 Ler Outro")
        self.btn_limpar.clicked.connect(self.limpar_campo)
        self.btn_fechar = QPushButton("⏹ Fechar")
        self.btn_fechar.clicked.connect(self.reject)

        linha_botoes.addWidget(self.btn_limpar)
        linha_botoes.addStretch()
        linha_botoes.addWidget(self.btn_fechar)
        layout.addLayout(linha_botoes)

        QTimer.singleShot(100, lambda: self.campo_codigo.setFocus())

    def quando_mudar_texto(self, texto):
        texto = texto.strip()
        if not texto:
            self.label_status.setText("✅ Pronto para ler!")
            self.label_status.setStyleSheet("color: green; font-weight: bold;")
            return

        self.label_status.setText("🔄 Processando...")
        self.label_status.setStyleSheet("color: blue; font-weight: bold;")

        ok, mensagem = registrar_devolucao_por_qrcode(texto)
        if ok:
            self.label_status.setText("✅ " + mensagem)
            self.label_status.setStyleSheet("color: green; font-weight: bold;")
            QMessageBox.information(self, "✅ Sucesso!", mensagem)
            self.accept()
        else:
            self.label_status.setText("❌ " + mensagem)
            self.label_status.setStyleSheet("color: red; font-weight: bold;")
            QTimer.singleShot(800, self.limpar_campo)

    def limpar_campo(self):
        self.campo_codigo.clear()
        self.label_status.setText("✅ Pronto para ler!")
        self.label_status.setStyleSheet("color: green; font-weight: bold;")
        QTimer.singleShot(100, lambda: self.campo_codigo.setFocus())

    def showEvent(self, evento):
        super().showEvent(evento)
        QTimer.singleShot(100, lambda: self.campo_codigo.setFocus())

# ═══════ FUNÇÕES AUXILIARES ═══════
def _parse_datetime(value):
    if not value or isinstance(value, datetime):
        return value
    texto = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%d/%m/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try: return datetime.strptime(texto, fmt)
        except Exception: pass
    try: return datetime.fromisoformat(texto.replace("Z", "+00:00"))
    except Exception: return None

def _esta_em_atraso(data_retirada, now=None):
    now = now or datetime.now()
    retirada_dt = _parse_datetime(data_retirada)
    return bool(retirada_dt and (now - retirada_dt).total_seconds() / 3600 >= ALERTA_HORAS)

def _normalizar_status(status):
    if not status: return ""
    s = str(status).strip().lower()
    return {"disponível":"disponivel","indisponível":"indisponivel"}.get(s, s)

def _normalizar_motivo_emprestimo(motivo):
    if motivo is None: return None
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
    finally: conn.close()
    if not row: return False, "Utilizador não encontrado."
    vinculo, data_fim, ativo = row
    if not ativo: return False, "Utilizador inativo."
    if str(vinculo or "").strip() == "Servidor(a)" or data_fim is None:
        return True, ""
    return (True, "") if date.today() <= data_fim else (False, f"Validade expirada em {data_fim.strftime('%d/%m/%Y')}")

def formatar_data_br(data_val):
    dt = _parse_datetime(data_val)
    return dt.strftime("%d/%m/%Y %H:%M:%S") if dt else ("" if data_val is None else str(data_val))

def obter_chave_fisica_disponivel_por_sala(sala_id, apenas_principal=False):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        sql = "SELECT id, etiqueta, tipo, status FROM chaves_fisicas WHERE sala_id = %s AND ativa = TRUE AND status = 'disponivel'"
        sql += " AND tipo = 'principal' LIMIT 1" if apenas_principal else " ORDER BY CASE tipo WHEN 'principal' THEN 0 WHEN 'reserva' THEN 1 ELSE 2 END, id LIMIT 1"
        cur.execute(sql, [sala_id])
        return cur.fetchone()
    finally: conn.close()

def pode_retirar_chave_fisica(chave_fisica_id):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, ativa, status FROM chaves_fisicas WHERE id = %s", (chave_fisica_id,))
        row = cur.fetchone()
    finally: conn.close()
    if not row: return False, "Chave física não encontrada."
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
            if data_ini: sql += " AND m.data_retirada >= %s"; params.append(data_ini)
            if data_fim: sql += " AND m.data_retirada <= %s"; params.append(data_fim)
        sql += " ORDER BY 2,4,5,6,7 DESC,8,9"
        cur.execute(sql, params)
        return cur.fetchall()
    finally: conn.close()

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
        if chave: sql += " AND COALESCE(cf.etiqueta, m.chave, '') ILIKE %s"; params.append(f"%{chave.strip()}%")
        if usuario: sql += " AND COALESCE(u.nome, m.usuario) ILIKE %s"; params.append(f"%{usuario.strip()}%")
        if data_ini: sql += " AND m.data_retirada >= %s"; params.append(data_ini)
        if data_fim: sql += " AND m.data_retirada <= %s"; params.append(data_fim)
        if status and status.lower() not in ["todos",""]: sql += " AND m.status = %s"; params.append(_normalizar_status(status))
        sql += " ORDER BY 2,4,5,6,7 DESC,8,9"
        cur.execute(sql, params)
        return cur.fetchall()
    finally: conn.close()

def salas_com_pelo_menos_uma_copia():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT sala_id FROM chaves_fisicas WHERE ativa=TRUE AND tipo='reserva'")
        return {r[0] for r in cur.fetchall()}
    finally: conn.close()

def registrar_retirada(sala_id, chave_fisica_id, utilizador_id, email, motivo_emprestimo=None):
    email = (email or "").strip().lower()
    motivo_emprestimo = _normalizar_motivo_emprestimo(motivo_emprestimo)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT nome, ativo FROM utilizadores WHERE id = %s", (utilizador_id,))
        nome_utilizador, ativo = cur.fetchone()
        if not ativo: raise ValueError("Utilizador inativo")
        cur.execute("SELECT id, sala_id, etiqueta, ativa, status FROM chaves_fisicas WHERE id = %s FOR UPDATE", (chave_fisica_id,))
        _, sala_id_chave, etiqueta, ativa_ch, status_ch = cur.fetchone()
        if sala_id_chave != sala_id or not ativa_ch or _normalizar_status(status_ch) != "disponivel":
            raise ValueError("Chave indisponível ou não pertence à sala")
        cur.execute("SELECT 1 FROM movimentacoes WHERE chave_fisica_id=%s AND status='indisponivel' AND data_retorno IS NULL LIMIT 1", (chave_fisica_id,))
        if cur.fetchone(): raise ValueError("Chave já retirada")
        chave_display = etiqueta or montar_display_sala_por_id(sala_id)
        cur.execute("""INSERT INTO movimentacoes (chave,chave_fisica_id,sala_id,utilizador_id,usuario,email,data_retirada,status,alerta_enviado,motivo_emprestimo)
            VALUES (%s,%s,%s,%s,%s,%s,NOW(),'indisponivel',FALSE,%s)""",
            (chave_display, chave_fisica_id, sala_id, utilizador_id, nome_utilizador, email, motivo_emprestimo))
        cur.execute("UPDATE salas SET status='indisponivel' WHERE id=%s", (sala_id,))
        cur.execute("UPDATE chaves_fisicas SET status='indisponivel', atualizada_em=NOW() WHERE id=%s", (chave_fisica_id,))
        conn.commit()
        return chave_display
    except Exception: conn.rollback(); raise
    finally: conn.close()

def registrar_devolucao(mov_id, sala_id=None):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT chave,chave_fisica_id,sala_id,status FROM movimentacoes WHERE id=%s FOR UPDATE", (mov_id,))
        chave, chave_fisica_id, sala_id_db, status_atual = cur.fetchone()
        if _normalizar_status(status_atual) == "disponivel":
            return chave or "", chave_fisica_id, sala_id_db
        sala_id_final = sala_id_db if sala_id is None else sala_id
        cur.execute("UPDATE movimentacoes SET data_retorno=NOW(),status='disponivel',alerta_enviado=FALSE WHERE id=%s", (mov_id,))
        if sala_id_final: cur.execute("UPDATE salas SET status='disponivel' WHERE id=%s", (sala_id_final,))
        if chave_fisica_id: cur.execute("UPDATE chaves_fisicas SET status='disponivel',atualizada_em=NOW() WHERE id=%s", (chave_fisica_id,))
        conn.commit()
        return chave or "", chave_fisica_id, sala_id_final
    except Exception: conn.rollback(); raise
    finally: conn.close()

class FiltroMovimentacaoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filtrar Movimentações")
        lyt = QFormLayout(self)
        self.data_inicio = QDateEdit(QDate.currentDate()); self.data_inicio.setDisplayFormat("dd/MM/yyyy"); self.data_inicio.setCalendarPopup(True)
        self.data_fim = QDateEdit(QDate.currentDate()); self.data_fim.setDisplayFormat("dd/MM/yyyy"); self.data_fim.setCalendarPopup(True)
        self.input_usuario = QLineEdit()
        self.combo_status = QComboBox(); self.combo_status.addItems(["Todos","disponível","indisponível"])
        lyt.addRow("Data Início:",self.data_inicio); lyt.addRow("Data Fim:",self.data_fim)
        lyt.addRow("Utilizador:",self.input_usuario); lyt.addRow("Status:",self.combo_status)
        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        btn.accepted.connect(self.accept); btn.rejected.connect(self.reject); lyt.addWidget(btn)
    def get_filters(self):
        ini = self.data_inicio.date().toString("yyyy-MM-dd")+" 00:00:00"
        fim = self.data_fim.date().toString("yyyy-MM-dd")+" 23:59:59"
        st = None if self.combo_status.currentText()=="Todos" else _normalizar_status(self.combo_status.currentText())
        return {"data_ini":ini,"data_fim":fim,"usuario":self.input_usuario.text().strip().lower() or None,"status":st}

class MovimentacoesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.sala_id_atual=None; self.filtro_atual=None; self.chave_fisica_id_atual=None
        self._em_operacao=False; self.filtro_apenas_copias=False
        self.utilizador_atual=get_current_user(); self.eh_admin=bool(self.utilizador_atual and self.utilizador_atual.get("is_admin"))
        self.init_ui()
        try: self.carregar_movimentacoes()
        except Exception as e: QMessageBox.critical(self,"Erro",f"Falha ao carregar:\n{e}")
        self.timer=QTimer(self); self.timer.timeout.connect(self.carregar_movimentacoes); self.timer.start(5000)

    def _get_dash_main(self):
        w=self.parentWidget()
        while w and w.__class__.__name__!="DashMain": w=w.parentWidget()
        return w

    def _notificar_operacao(self,msg):
        d=self._get_dash_main()
        if d and hasattr(d,"show_operation_done"): d.show_operation_done(msg)

    def _preservar_mov_id_selecionado(self):
        sel=self.table.selectionModel().selectedRows()
        return self.table.item(sel[0].row(),0).text().strip() if sel else None

    def _restaurar_selecao_por_mov_id(self,mid):
        if not mid: return
        for r in range(self.table.rowCount()):
            if self.table.item(r,0) and self.table.item(r,0).text().strip()==str(mid):
                self.table.selectRow(r); break

    def acao_verificar_pendencias(self):
        qtd=verificar_pendencias_e_enviar_emails()
        QMessageBox.information(self,"Pendências",f"{qtd} pendência(s) em atraso." if qtd else "Nenhuma pendência em atraso.")

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(QLabel("<h2>Movimentações de Chaves/Salas</h2>"))
        # ✅ ETIQUETA CLICÁVEL DE PENDÊNCIAS
        self.label_pendencias = self._criar_label_pendencias()
        layout.addWidget(self.label_pendencias)


        estilo_botao = """
        QPushButton {
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
            min-height: 22px;
        }
        """
        estilo_laranja = """
        QPushButton {
            background-color: #ff9900;
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
            min-height: 22px;
        }
        QPushButton:hover { background-color: #e68a00; }
        """
        estilo_verde = """
        QPushButton {
            background-color: #28a745;
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
            min-height: 22px;
        }
        QPushButton:hover { background-color: #218838; }
        """
        estilo_azul = """
        QPushButton {
            background-color: #007bff;
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
            min-height: 22px;
        }
        QPushButton:hover { background-color: #0069d9; }
        """
        estilo_cinza = """
        QPushButton {
            background-color: #f8f9fa;
            border: 1px solid #ccc;
            padding: 6px 12px;
            border-radius: 4px;
            min-height: 22px;
        }
        QPushButton:hover { background-color: #e9ecef; }
        """

        linha1 = QHBoxLayout()
        linha1.setSpacing(10)

        self.label_sala_selecionada = QLineEdit()
        self.label_sala_selecionada.setReadOnly(True)
        self.label_sala_selecionada.setPlaceholderText("Nenhuma sala selecionada")
        self.btn_escolher_sala = QPushButton("Selecionar sala...")
        self.btn_escolher_sala.setStyleSheet(estilo_cinza)
        self.btn_escolher_sala.clicked.connect(self.abrir_dialogo_salas)

        self.combo_utilizador = QComboBox()
        self.combo_utilizador.setMinimumWidth(220)

        self.btn_novo_utilizador = QPushButton("+ Utilizador")
        self.btn_novo_utilizador.setStyleSheet(estilo_laranja)
        self.btn_novo_utilizador.clicked.connect(self.cadastrar_utilizador_rapido)

        self.combo_motivo = QComboBox()
        self.combo_motivo.addItem("Normal", "normal")
        self.combo_motivo.addItem("Cópia temporária", "copia_temporaria")
        self.combo_motivo.addItem("Extravio", "extravio")
        self.combo_motivo.addItem("Não devolvida", "nao_devolvida")
        self.combo_motivo.addItem("Contingência", "contingencia")

        self.btn_retirar = QPushButton("Registrar Retirada")
        self.btn_retirar.setStyleSheet(estilo_verde)
        self.btn_retirar.clicked.connect(self.adicionar_movimentacao)

        self.btn_devolver = QPushButton("Registrar Devolução")
        self.btn_devolver.setStyleSheet(estilo_azul)
        self.btn_devolver.clicked.connect(self.devolver_selecionada)

        linha1.addWidget(QLabel("Sala:"))
        linha1.addWidget(self.label_sala_selecionada, stretch=1)
        linha1.addWidget(self.btn_escolher_sala)
        linha1.addWidget(self.combo_utilizador)
        linha1.addWidget(self.btn_novo_utilizador)
        linha1.addWidget(QLabel("Motivo:"))
        linha1.addWidget(self.combo_motivo)
        linha1.addWidget(self.btn_retirar)
        linha1.addWidget(self.btn_devolver)
        layout.addLayout(linha1)

        linha2 = QHBoxLayout()
        linha2.setSpacing(10)
        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_filtrar.setStyleSheet(estilo_cinza)
        self.btn_filtrar.clicked.connect(self.abrir_filtro_modal)

        self.btn_verificar_pendencias = QPushButton("Verificar pendências")
        self.btn_verificar_pendencias.setStyleSheet(estilo_cinza)
        self.btn_verificar_pendencias.clicked.connect(self.acao_verificar_pendencias)

        linha2.addWidget(self.btn_filtrar)
        linha2.addWidget(self.btn_verificar_pendencias)
        linha2.addStretch()
        layout.addLayout(linha2)

        linha3 = QHBoxLayout()
        linha3.setSpacing(10)

        self.btn_exportar_csv = QPushButton("Exportar CSV")
        self.btn_exportar_csv.setStyleSheet(estilo_cinza)
        self.btn_exportar_csv.clicked.connect(self.exportar_csv)

        self.btn_exportar_pdf = QPushButton("Exportar PDF")
        self.btn_exportar_pdf.setStyleSheet(estilo_cinza)
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)

        self.btn_gerar_etiquetas = QPushButton("🖨️ Gerar Etiquetas QR")
        self.btn_gerar_etiquetas.setStyleSheet(estilo_cinza)
        self.btn_gerar_etiquetas.clicked.connect(self.acao_gerar_etiquetas)

        # ✅ BOTÃO AJUSTADO — renomeado, com estilo e função de aviso RFID
        self.btn_ler_qrcode = QPushButton("📷 Leitura QR → Em implantação RFID")
        self.btn_ler_qrcode.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                color: #888;
                border: 1px solid #ccc;
                padding: 6px 12px;
                border-radius: 4px;
                min-height: 22px;
            }
        """)
        self.btn_ler_qrcode.clicked.connect(self.aviso_rfid)

        linha3.addWidget(self.btn_exportar_csv)
        linha3.addWidget(self.btn_exportar_pdf)
        linha3.addWidget(self.btn_gerar_etiquetas)
        linha3.addWidget(self.btn_ler_qrcode)
        linha3.addStretch()
        layout.addLayout(linha3)

        colunas = ["ID", "Chave", "Chave física ID", "Descrição sala", "Utilizador", "Vínculo",
                   "Retirada", "Devolução", "Status", "Tipo", "Motivo", "Aviso"]
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

        self.load_utilizadores_combo()
        # Atualiza etiqueta sempre que recarrega a tabela
        self._atualizar_contagem_pendencias()

    def abrir_dialogo_salas(self):
        dlg=SelecionarSalaDialog(self, is_admin=self.eh_admin)
        if dlg.exec()!=QDialog.DialogCode.Accepted or dlg.sala_id_selecionada is None: return
        self.sala_id_atual=dlg.sala_id_selecionada; self.label_sala_selecionada.setText(dlg.sala_display_selecionada or "")
        if self.eh_admin and getattr(dlg,"apenas_copias_reserva",False):
            self.filtro_apenas_copias=True; busca_principal=True
        else:
            self.filtro_apenas_copias=False; busca_principal=False
        chave_row=obter_chave_fisica_disponivel_por_sala(self.sala_id_atual, apenas_principal=busca_principal)
        self.chave_fisica_id_atual=chave_row[0] if chave_row else None

    def load_utilizadores_combo(self):
        self.combo_utilizador.clear()
        conn=get_db_connection()
        try:
            cur=conn.cursor(); cur.execute("SELECT id,COALESCE(nome,''),COALESCE(email,'') FROM utilizadores WHERE ativo=TRUE ORDER BY nome")
            self.combo_utilizador.addItem("Selecione...",None)
            for uid,nome,email in cur.fetchall(): self.combo_utilizador.addItem(nome,{"id":uid,"email":email})
        finally: conn.close()

    def cadastrar_utilizador_rapido(self):
        from admin.utilizadores_tab import UtilizadorDialog
        dlg=UtilizadorDialog(self)
        if dlg.exec():
            d=dlg.get_dados(); nome=(d.get("nome") or "").strip(); email=(d.get("email") or "").strip().lower()
            if not nome or not email or not email_valido(email): QMessageBox.warning(self,"Erro","Nome e e-mail válido obrigatórios."); return
            conn=get_db_connection()
            try:
                cur=conn.cursor(); cur.execute("INSERT INTO utilizadores (nome,email,ativo) VALUES (%s,%s,TRUE) RETURNING id",(nome,email))
                novo_id=cur.fetchone()[0]; conn.commit()
            except Exception as e: conn.rollback(); QMessageBox.critical(self,"Erro",f"Falha: {e}"); return
            finally: conn.close()
            self.load_utilizadores_combo()
            for i in range(self.combo_utilizador.count()):
                d=self.combo_utilizador.itemData(i)
                if d and d.get("id")==novo_id: self.combo_utilizador.setCurrentIndex(i); break
            self._notificar_operacao("Utilizador cadastrado!")

    def abrir_filtro_modal(self):
        dlg=FiltroMovimentacaoDialog(self)
        if dlg.exec(): self.filtro_atual=dlg.get_filters(); self.carregar_movimentacoes()

    def abrir_leitura_qrcode(self):
        dlg=LeituraQRDialog(self)
        if dlg.exec(): self.carregar_movimentacoes(); self._notificar_operacao("✅ Devolução registrada via QR Code!")

    # ✅ FUNÇÃO DE AVISO RFID — nova função adicionada
    def aviso_rfid(self):
        """Aviso: Leitura QR será substituída por RFID"""
        QMessageBox.information(self, "ℹ️ Em Desenvolvimento",
            "A leitura por QR Code será substituída por leitura RFID.\n\n"
            "Aguarde a próxima atualização do sistema.")

    def acao_gerar_etiquetas(self):
        """Abre janela para escolher forma de geração: Todas, Lote ou Individual"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QListWidget, QListWidgetItem, QAbstractItemView

        class EscolhaEtiquetasDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("🖨️ Gerar Etiquetas QR")
                self.setMinimumSize(520, 420)
                self.escolha = None
                self.chaves_selecionadas = []

                layout = QVBoxLayout(self)

                self.radio_todas = QRadioButton("📋 Gerar de TODAS as chaves cadastradas")
                self.radio_todas.setChecked(True)
                self.radio_lote = QRadioButton("✅ Selecionar VÁRIAS chaves (em lote)")
                self.radio_individual = QRadioButton("📄 Apenas UMA chave (individual)")

                layout.addWidget(self.radio_todas)
                layout.addWidget(self.radio_lote)
                layout.addWidget(self.radio_individual)

                self.lista_chaves = QListWidget()
                self.lista_chaves.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
                self.lista_chaves.setVisible(False)
                layout.addWidget(self.lista_chaves)

                self._carregar_chaves()

                from PyQt6.QtWidgets import QPushButton
                self.btn_confirmar = QPushButton("➡️ Continuar")
                self.btn_cancelar = QPushButton("Cancelar")
                layout.addWidget(self.btn_confirmar)
                layout.addWidget(self.btn_cancelar)

                self.radio_todas.toggled.connect(self._atualizar_visibilidade)
                self.radio_lote.toggled.connect(self._atualizar_visibilidade)
                self.radio_individual.toggled.connect(self._atualizar_visibilidade)
                self.btn_confirmar.clicked.connect(self._confirmar)
                self.btn_cancelar.clicked.connect(self.reject)

                self._atualizar_visibilidade()

            def _atualizar_visibilidade(self):
                mostrar_lista = self.radio_lote.isChecked() or self.radio_individual.isChecked()
                self.lista_chaves.setVisible(mostrar_lista)
                if self.radio_individual.isChecked():
                    self.lista_chaves.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
                else:
                    self.lista_chaves.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

            def _carregar_chaves(self):
                conn = get_db_connection()
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT cf.id, cf.etiqueta, s.nome, s.descricao, cf.tipo FROM chaves_fisicas cf LEFT JOIN salas s ON cf.sala_id = s.id WHERE cf.ativa = TRUE ORDER BY cf.etiqueta")
                    for cid, et, sa_nome, sa_desc, tipo in cur.fetchall():
                        sala_display = f"{sa_nome} - {sa_desc}" if sa_desc else (sa_nome or "Sem sala")
                        item = QListWidgetItem(f"{et} | {sala_display} | {tipo.upper()}")
                        item.setData(1000, {"id": cid, "etiqueta": et, "sala_nome": sala_display, "tipo": tipo})
                        self.lista_chaves.addItem(item)
                finally: conn.close()

            def _confirmar(self):
                if self.radio_todas.isChecked():
                    self.escolha = "todas"
                    self.chaves_selecionadas = None
                elif self.radio_lote.isChecked():
                    self.escolha = "lote"
                    self.chaves_selecionadas = [item.data(1000) for item in self.lista_chaves.selectedItems()]
                    if not self.chaves_selecionadas:
                        QMessageBox.warning(self, "Atenção", "Selecione pelo menos uma chave na lista!")
                        return
                else:
                    self.escolha = "individual"
                    itens = self.lista_chaves.selectedItems()
                    if not itens:
                        QMessageBox.warning(self, "Atenção", "Selecione uma chave na lista!")
                        return
                    self.chaves_selecionadas = [itens[0].data(1000)]
                self.accept()

        dlg = EscolhaEtiquetasDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        if dlg.escolha == "todas":
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT cf.id, cf.etiqueta, s.nome, s.descricao, cf.tipo FROM chaves_fisicas cf LEFT JOIN salas s ON cf.sala_id = s.id WHERE cf.ativa = TRUE ORDER BY cf.etiqueta")
                chaves = []
                for cid, et, sa_nome, sa_desc, tipo in cur.fetchall():
                    chaves.append({"id": cid, "etiqueta": et,
                                   "sala_nome": f"{sa_nome} - {sa_desc}" if sa_desc else (sa_nome or "Sem sala"),
                                   "tipo": tipo})
            finally: conn.close()
        else:
            chaves = dlg.chaves_selecionadas

        if not chaves:
            QMessageBox.information(self, "Aviso", "Nenhuma chave selecionada.")
            return

        cam, _ = QFileDialog.getSaveFileName(self, "Salvar Etiquetas QR", "", "PDF (*.pdf)")
        if cam:
            gerar_etiquetas_pdf(cam, chaves)
            QMessageBox.information(self, "✅ Sucesso!",
                                    f"Etiquetas salvas em:\n{cam}\n\nQuantidade: {len(chaves)} etiqueta(s)")
            self._notificar_operacao(f"Etiquetas QR geradas: {len(chaves)} chave(s)")

    def carregar_movimentacoes(self):
        if self._em_operacao: return
        try:
            mid_sel=self._preservar_mov_id_selecionado()
            dados=listar_movimentacoes() if self.filtro_atual is None else buscar_movimentacoes_personalizado(**self.filtro_atual)
            if self.eh_admin and self.filtro_apenas_copias:
                sc=salas_com_pelo_menos_uma_copia(); dados=[r for r in dados if r[12] in sc]
            self.exibir_historico(dados); self._restaurar_selecao_por_mov_id(mid_sel)
        except Exception as e: print(f"Erro carregar: {e}")

    def exibir_historico(self,hist):
        self.table.setRowCount(0); agora=datetime.now()
        for idx,linha in enumerate(hist):
            linha=list(linha); aviso=linha.pop()
            if not self.eh_admin: linha.pop(9)
            self.table.insertRow(idx)
            for c,v in enumerate(linha):
                if c in (6,7): v=formatar_data_br(v)
                txt=str(v) if v is not None else ""
                it=QTableWidgetItem(txt); it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if c==8:
                    st=_normalizar_status(v); ret=linha[6]
                    aplicar_cor_status_item_generico(it,st,ret,linha[7],agora)
                    if st=="indisponivel" and _esta_em_atraso(ret,agora):
                        it.setBackground(QBrush(QColor("#ffcccc"))); it.setForeground(QBrush(QColor("#b71c1c")))
                self.table.setItem(idx,c,it)
            aviso_item=QTableWidgetItem("✅" if aviso else "❌"); aviso_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            aviso_item.setToolTip("Enviado" if aviso else "Não enviado")
            self.table.setItem(idx,self.table.columnCount()-1,aviso_item)

    def adicionar_movimentacao(self):
        sid=self.sala_id_atual; du=self.combo_utilizador.currentData() or {}; uid=du.get("id"); email=(du.get("email") or "").strip().lower()
        mot=self.combo_motivo.currentData(); op=(get_current_user() or {}).get("login","sistema")
        if not sid or uid is None: QMessageBox.warning(self,"Atenção","Selecione sala e utilizador."); return
        ok,msg=pode_solicitar_retirada(uid)
        if not ok: QMessageBox.warning(self,"Bloqueado",msg); return
        if email and not email_valido(email): QMessageBox.warning(self,"Erro","E-mail inválido."); return
        chave_row=obter_chave_fisica_disponivel_por_sala(sid, apenas_principal=not self.filtro_apenas_copias)
        if not chave_row: QMessageBox.warning(self,"Sem chave","Nenhuma chave disponível."); return
        cfid=chave_row[0]; ok,msg=pode_retirar_chave_fisica(cfid)
        if not ok: QMessageBox.warning(self,"Atenção",msg); return
        self._em_operacao=True; self.timer.stop()
        try:
            chave=registrar_retirada(sid,cfid,uid,email,mot)
            log_acao("retirada",op,chave,"sucesso",f"sala={sid} chave={cfid}")
            self.sala_id_atual=None; self.chave_fisica_id_atual=None; self.label_sala_selecionada.clear()
            self.combo_utilizador.setCurrentIndex(0); self.combo_motivo.setCurrentIndex(0)
            self.carregar_movimentacoes(); self._notificar_operacao(f"Retirada: {chave}")
        except Exception as e: QMessageBox.critical(self,"Erro",f"Falha: {e}"); log_acao("retirada",op,f"sala={sid}","erro",str(e))
        finally: self._em_operacao=False; self.timer.start(5000)

    def devolver_selecionada(self):
        sel=self.table.selectionModel().selectedRows(); op=(get_current_user() or {}).get("login","sistema")
        if not sel: QMessageBox.warning(self,"Atenção","Selecione uma linha."); return
        r=sel[0].row(); mid=self.table.item(r,0).text().strip(); chave=self.table.item(r,1).text().strip()
        st=_normalizar_status(self.table.item(r,8).text())
        if not mid.isdigit(): QMessageBox.warning(self,"Erro","ID inválido."); return
        if st=="disponivel": QMessageBox.information(self,"OK","Já devolvida."); return
        self._em_operacao=True; self.timer.stop()
        try:
            chave,cfid,sid=registrar_devolucao(int(mid))
            log_acao("devolucao",op,chave,"sucesso",f"mid={mid} sala={sid}")
            self.carregar_movimentacoes(); self._notificar_operacao(f"Devolvida: {chave}")
        except Exception as e: QMessageBox.critical(self,"Erro",f"Falha: {e}"); log_acao("devolucao",op,chave,"erro",str(e))
        finally: self._em_operacao=False; self.timer.start(5000)

    def obter_dados_da_tabela(self):
        return [[(self.table.item(r,c).text() if self.table.item(r,c) else "") for c in range(self.table.columnCount())] for r in range(self.table.rowCount())]

    def exportar_csv(self):
        cam,_=QFileDialog.getSaveFileName(self,"Salvar CSV","","CSV (*.csv)")
        if not cam: return
        dados=self.obter_dados_da_tabela()
        cab=[self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        with open(cam,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f,delimiter=";"); w.writerow(cab); w.writerows(dados)
        self._notificar_operacao("CSV salvo!")

    def exportar_pdf(self):
        cam, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "", "PDF (*.pdf)")
        if not cam:
            return
        dados = self.obter_dados_da_tabela()
        cab = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        est = getSampleStyleSheet()["BodyText"]
        est.fontSize = 8
        est.leading = 10
        est.fontName = "Helvetica"
        linhas = [cab]
        for l in dados:
            linhas.append([Paragraph(str(c).replace("&", "&amp;") if c else "", est) for c in l])
        doc = SimpleDocTemplate(cam, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20,
                                bottomMargin=20)
        larg = [28, 80, 55, 130, 100, 70, 85, 85, 70, 55, 85, 50] if self.eh_admin else [28, 80, 55, 130, 100, 70, 85,
                                                                                         85, 70, 85, 50]
        t = Table(linhas, repeatRows=1, colWidths=larg)
        t.setStyle(TableStyle([
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
        doc.build([Paragraph("Relatório de Movimentações", getSampleStyleSheet()["Title"]), Spacer(1, 12), t])
        self._notificar_operacao("PDF salvo!")

    def _criar_label_pendencias(self):
        self.label_pendencias = QLabel("🔄 Verificando pendências...")
        self.label_pendencias.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_pendencias.setCursor(Qt.CursorShape.PointingHandCursor)
        self.label_pendencias.setStyleSheet("""
            QLabel { padding: 6px 12px; border-radius: 6px; font-weight: bold; font-size: 13px; }
            QLabel:hover { background-color: #e9ecef; }
        """)
        self.label_pendencias.mousePressEvent = self._abrir_janela_pendencias_clicada
        return self.label_pendencias

    def _atualizar_contagem_pendencias(self):
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""SELECT COUNT(*) FROM movimentacoes
                WHERE status = 'indisponivel' AND data_retorno IS NULL AND alerta_enviado = FALSE""")
            total = cur.fetchone()[0]
        except Exception:
            total = 0
        finally:
            conn.close()

        if total == 0:
            self.label_pendencias.setText("✅ Nenhuma chave em atraso")
            self.label_pendencias.setStyleSheet("""
                QLabel { padding: 6px 12px; border-radius: 6px; font-weight: bold; font-size: 13px;
                background-color: #d4edda; color: #155724; }""")
            self.label_pendencias.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.label_pendencias.setText(f"⚠️ {total} chave(s) em atraso — Clique para notificar")
            self.label_pendencias.setStyleSheet("""
                QLabel { padding: 6px 12px; border-radius: 6px; font-weight: bold; font-size: 13px;
                background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                QLabel:hover { background-color: #f1b0b7; }""")
            self.label_pendencias.setCursor(Qt.CursorShape.PointingHandCursor)

    def _abrir_janela_pendencias_clicada(self, event):
        if "Nenhuma" in self.label_pendencias.text():
            QMessageBox.information(self, "Pendências", "✅ Sem chaves em atraso.")
            return
        verificar_pendencias_e_enviar_emails()
        self._atualizar_contagem_pendencias()
def ha_chaves_em_atraso():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT data_retirada FROM movimentacoes WHERE status='indisponivel' AND data_retorno IS NULL")
        return any(_esta_em_atraso(row[0]) for row in cur.fetchall())
    finally:
        conn.close()


# ═══════ JANELA DE CONFIRMAÇÃO DE ENVIO DE E-MAILS ═══════
class JanelaConfirmarEnvioEmAtraso(QDialog):
    def __init__(self, lista_pendencias, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 Pendências em Atraso — Confirmação de Envio")
        self.setMinimumSize(950, 500)
        self.lista_pendencias = lista_pendencias
        self.lista_selecionada = []

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        layout.addWidget(QLabel("<h3>As seguintes chaves estão em atraso e seriam notificadas:</h3>"))
        layout.addWidget(QLabel("✅ Marque quais devem receber e-mail. Desmarque para NÃO enviar."))

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Enviar?", "ID Mov.", "Chave/Sala", "Utilizador", "E-mail",
            "Retirada", "Horas em Atraso"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._preencher_tabela()
        layout.addWidget(self.table)

        botoes_linha = QHBoxLayout()
        self.btn_marcar_todos = QPushButton("✅ Marcar Todos")
        self.btn_marcar_todos.clicked.connect(self._marcar_todos)
        self.btn_desmarcar_todos = QPushButton("❌ Desmarcar Todos")
        self.btn_desmarcar_todos.clicked.connect(self._desmarcar_todos)
        botoes_linha.addWidget(self.btn_marcar_todos)
        botoes_linha.addWidget(self.btn_desmarcar_todos)
        botoes_linha.addStretch()
        layout.addLayout(botoes_linha)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Ok).setText("📤 Enviar Selecionados")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.accepted.connect(self._coletar_selecao_e_aceitar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def _preencher_tabela(self):
        self.table.setRowCount(0)
        for linha, item in enumerate(self.lista_pendencias):
            self.table.insertRow(linha)
            chk = QCheckBox()
            chk.setChecked(True)
            self.table.setCellWidget(linha, 0, chk)
            self.table.setItem(linha, 1, QTableWidgetItem(str(item["mov_id"])))
            self.table.setItem(linha, 2, QTableWidgetItem(item["chave"]))
            self.table.setItem(linha, 3, QTableWidgetItem(item["usuario"]))
            self.table.setItem(linha, 4, QTableWidgetItem(item["email"] or "❌ Sem e-mail"))
            self.table.setItem(linha, 5, QTableWidgetItem(item["data_retirada_fmt"]))
            self.table.setItem(linha, 6, QTableWidgetItem(f"{item['horas_atraso']:.1f} h"))
            if not item["email"]:
                for c in range(1, 7):
                    cel = self.table.item(linha, c)
                    if cel: cel.setBackground(QBrush(QColor("#fff3cd")))

    def _marcar_todos(self):
        for r in range(self.table.rowCount()):
            chk = self.table.cellWidget(r, 0)
            if chk: chk.setChecked(True)

    def _desmarcar_todos(self):
        for r in range(self.table.rowCount()):
            chk = self.table.cellWidget(r, 0)
            if chk: chk.setChecked(False)

    def _coletar_selecao_e_aceitar(self):
        self.lista_selecionada = []
        for r in range(self.table.rowCount()):
            chk = self.table.cellWidget(r, 0)
            if chk and chk.isChecked():
                self.lista_selecionada.append(self.lista_pendencias[r])
        self.accept()


def verificar_pendencias_e_enviar_emails():
    conn = get_db_connection()
    lista_pendencias = []
    agora = datetime.now()
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

        for mov_id, chave, usuario, email, dt_retirada, alerta_enviado in linhas:
            if alerta_enviado:
                continue
            dt = _parse_datetime(dt_retirada)
            if not dt:
                continue
            horas_atraso = (agora - dt).total_seconds() / 3600
            if horas_atraso < ALERTA_HORAS:
                continue
            lista_pendencias.append({
                "mov_id": mov_id,
                "chave": chave,
                "usuario": usuario or "Desconhecido",
                "email": (email or "").strip().lower() or None,
                "data_retirada": dt_retirada,
                "data_retirada_fmt": formatar_data_br(dt_retirada),
                "horas_atraso": horas_atraso
            })

        if not lista_pendencias:
            QMessageBox.information(None, "Pendências", "✅ Nenhuma chave em atraso para notificar.")
            return 0

        janela = JanelaConfirmarEnvioEmAtraso(lista_pendencias)
        if janela.exec() != QDialog.DialogCode.Accepted:
            QMessageBox.information(None, "Cancelado", "❌ Envio cancelado pelo usuário.")
            return 0

        selecionadas = janela.lista_selecionada
        if not selecionadas:
            QMessageBox.information(None, "Aviso", "Nenhuma pendência foi marcada para envio.")
            return 0

        enviados = 0
        for item in selecionadas:
            mov_id = item["mov_id"]
            chave = item["chave"]
            usuario = item["usuario"]
            email = item["email"]
            dt_retirada = item["data_retirada"]

            if not email:
                msg_erro = "E-mail não cadastrado no utilizador"
                cur.execute("UPDATE movimentacoes SET alerta_erro = %s WHERE id = %s", (msg_erro, mov_id))
                conn.commit()
                log_acao("verificar_pendencias", "sistema", chave, "aviso", msg_erro)
                continue

            if not email_valido(email):
                msg_erro = f"E-mail inválido: {email}"
                cur.execute("UPDATE movimentacoes SET alerta_erro = %s WHERE id = %s", (msg_erro, mov_id))
                conn.commit()
                log_acao("verificar_pendencias", "sistema", chave, "erro", msg_erro)
                continue

            assunto = f"⚠️ Aviso de Atraso — Chave {chave}"
            corpo = f"""<html><body style="font-family:Arial,sans-serif;font-size:14px;">
            <h2 style="color:#d32f2f;">Aviso de Atraso na Devolução</h2>
            <p>Prezado(a) <strong>{usuario}</strong>,</p>
            <p>A chave <strong>{chave}</strong> encontra-se em atraso desde <strong>{formatar_data_br(dt_retirada)}</strong>.</p>
            <p>Por favor, devolva a chave o mais rápido possível.</p>
            <p>Atenciosamente,<br>Controle de Chaves — IFRS Alvorada</p>
            </body></html>"""

            ok, mensagem = enviar_email(email, assunto, corpo)
            if ok:
                cur.execute("""UPDATE movimentacoes
                    SET alerta_enviado = TRUE, alerta_enviado_em = CURRENT_TIMESTAMP, alerta_erro = NULL
                    WHERE id = %s""", (mov_id,))
                log_acao("verificar_pendencias", "sistema", chave, "sucesso", f"E-mail enviado para {email}")
                enviados += 1
            else:
                cur.execute("UPDATE movimentacoes SET alerta_erro = %s WHERE id = %s", (mensagem, mov_id))
                log_acao("verificar_pendencias", "sistema", chave, "erro", f"Falha: {mensagem}")
            conn.commit()

        QMessageBox.information(None, "Concluído",
            f"✅ Processo finalizado!\n\nTotal selecionado: {len(selecionadas)}\nE-mails enviados: {enviados}")
        return enviados

    except Exception as e:
        QMessageBox.critical(None, "Erro", f"Falha no processo:\n{str(e)}")
        return 0
    finally:
        conn.close()