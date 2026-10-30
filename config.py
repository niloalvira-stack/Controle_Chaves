import os
from utils.resources import resource_path
from utils.config_app import get_email_config, get_app_config
from autenticacao.helpers_autenticacao import get_db_connection

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app_cfg = get_app_config()
email_cfg = get_email_config()

APP_NAME = app_cfg["app_name"]
APP_VERSION = app_cfg["app_version"]
APP_DEVELOPER = app_cfg["app_developer"]
APP_COMPANY = app_cfg["app_company"]
APP_COPYRIGHT = "© 2025 Todos os direitos reservados."

APP_LOGO_PATH = resource_path(os.path.join("assets", "logo.png"))

COLOR_STATUS_DISPONIVEL = "#66ff66"
COLOR_STATUS_INDISPONIVEL = "#ffff66"
COLOR_STATUS_ATRASO = "#ff4d4d"

COLOR_BTN_AZUL = "#1976d2"
COLOR_BTN_VERDE = "#2e7d32"
COLOR_BTN_LARANJA = "#ffa000"
COLOR_BTN_VERMELHO = "#c62828"
COLOR_BTN_AMARELO = "#ffeb3b"

COLOR_BTN_TEXTO = "#ffffff"
COLOR_BTN_TEXTO_ESCURO = "#333333"

SMTP_SERVER = email_cfg["smtp_server"]
SMTP_PORT = email_cfg["smtp_port"]
EMAIL_REMETENTE = email_cfg["email_remetente"]
SMTP_USUARIO = email_cfg["smtp_usuario"]
SMTP_SENHA = email_cfg["smtp_senha"]

# ⚠️ EMAIL_ENVIO_AUTOMATICO NÃO É MAIS USADO — agora vem do banco!
# Mantido aqui apenas para compatibilidade temporária
EMAIL_ENVIO_AUTOMATICO = True


def carregar_modo_email():
    """Carrega do BANCO — único para TODOS os clientes"""
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT valor FROM configuracoes WHERE chave = 'modo_envio_email'")
            linha = cur.fetchone()
            cur.close()
            conn.close()
            if linha:
                return linha[0]
    except Exception as e:
        print(f"⚠️ Erro ao carregar modo de envio: {e}")
    return "automatico"  # Valor padrão


def salvar_modo_email(modo):
    """Salva no BANCO — reflete imediatamente para TODOS os clientes"""
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO configuracoes (chave, valor) VALUES (%s, %s)
                ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor
            """, ('modo_envio_email', modo))
            conn.commit()
            cur.close()
            conn.close()
        print(f"✅ Modo de envio alterado para: {modo}")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao salvar modo de envio: {e}")
        return False