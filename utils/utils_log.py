# utils/utils_log.py
import os
from datetime import datetime

# Pasta base do projeto (diretório deste arquivo -> sobe um nível)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# Caminho absoluto do arquivo de log
LOG_FILE = os.path.join(BASE_DIR, "controle_chaves.log")


def log_acao(mensagem: str):
    """
    Registra uma linha no arquivo de log com data/hora em padrão brasileiro.
    Exemplo:
    [27/11/2025 15:10:23] Mensagem aqui
    """
    try:
        datahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datahora}] {mensagem}\n")
    except Exception as e:
        print(f"Falha ao gravar log: {e}")
