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