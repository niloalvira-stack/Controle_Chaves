# utils/utils_log.py
import os
from datetime import datetime

# Pasta base do projeto
BASE_DIR = r"C:\Controle_Chaves"

# Caminho absoluto do arquivo de log
LOG_FILE = os.path.join(BASE_DIR, "controle_chaves.log")


def log_acao(mensagem: str):
    """
    Registra uma linha no arquivo de log com data/hora em padrão brasileiro.
    Exemplo de saída:
    [27/11/2025 15:10:23] Mensagem aqui
    """
    try:
        datahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datahora}] {mensagem}\n")
    except Exception as e:
        # Evita quebrar a aplicação por erro no log.
        # Se quiser, pode imprimir no console:
        print(f"Falha ao gravar log: {e}")
