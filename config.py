# config.py
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

APP_NAME = "Controle de Chaves"
APP_VERSION = "1.0.0"
APP_DEVELOPER = "Nilo Alvira"
APP_COMPANY = "IFRS-Campus Alvorada / DTI"
APP_COPYRIGHT = "© 2025 Todos os direitos reservados."
APP_LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")

# ----------------- PALETA DE CORES -----------------

# Status de chaves
COLOR_STATUS_DISPONIVEL = "#66ff66"      # verde claro
COLOR_STATUS_INDISPONIVEL = "#ffff66"    # amarelo
COLOR_STATUS_ATRASO = "#ff4d4d"          # vermelho

# Botões principais
COLOR_BTN_AZUL    = "#1976d2"
COLOR_BTN_VERDE   = "#2e7d32"
COLOR_BTN_LARANJA = "#ffa000"
COLOR_BTN_VERMELHO = "#c62828"
COLOR_BTN_AMARELO = "#ffeb3b"

# Cores de texto dos botões
COLOR_BTN_TEXTO = "#ffffff"
COLOR_BTN_TEXTO_ESCURO = "#333333"
