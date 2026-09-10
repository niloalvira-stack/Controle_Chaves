import os
from utils.resources import resource_path
from utils.config_app import get_email_config, get_app_config

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

## Modo de envio de avisos de atraso
# True  = Automático → envia sozinho após o limite de horas
# False = Manual     → abre tela para você escolher quais enviar
EMAIL_ENVIO_AUTOMATICO = True

# Caminho do arquivo de configuração (para salvar a escolha)
import json
from pathlib import Path
ARQUIVO_CONFIG = Path(__file__).parent / "config_status.json"

def carregar_modo_email():
    """Carrega a preferência salva, ou usa padrão"""
    if ARQUIVO_CONFIG.exists():
        try:
            with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
                dados = json.load(f)
                return dados.get("EMAIL_ENVIO_AUTOMATICO", True)
        except:
            return True
    return True

def salvar_modo_email(modo: bool):
    """Salva a preferência no arquivo"""
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump({"EMAIL_ENVIO_AUTOMATICO": modo}, f)