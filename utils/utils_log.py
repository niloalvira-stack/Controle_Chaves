import os
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_PATH = os.path.join(LOG_DIR, "app_audit.log")

# Alias para compatibilidade com o código antigo (admin.py)
LOG_FILE = LOG_PATH


def log_acao(
    action,
    user=None,
    resource=None,
    status="success",
    details=None,
):
    """
    Log de auditoria em formato chave=valor.

    Exemplo de linha gerada:
    time=2025-12-19T10:32:01 action=retirada user=admin resource="Sala 101 - CH001" status=success details="Retirada registrada"
    """
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    parts = [
        f"time={timestamp}",
        f"action={action}",
        f"status={status}",
    ]

    if user:
        parts.append(f"user={user}")
    if resource:
        # coloca recurso entre aspas para permitir espaços
        safe_resource = str(resource).replace('"', "'")
        parts.append(f'resource="{safe_resource}"')
    if details:
        safe_details = str(details).replace('"', "'")
        parts.append(f'details="{safe_details}"')

    line = " ".join(parts)

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
