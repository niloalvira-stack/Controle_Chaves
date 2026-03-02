import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import threading


# =========================
# Diretórios base / logs
# =========================

def get_base_dir():
    """
    Retorna o diretório base da aplicação.

    - No .exe (PyInstaller): pasta do executável (dist\\)
    - No modo desenvolvimento: pasta pai do arquivo atual
    """
    if getattr(sys, "frozen", False):
        # Executável gerado pelo PyInstaller
        return os.path.dirname(sys.executable)
    # Desenvolvimento
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


BASE_DIR = Path(get_base_dir())
LOG_DIR = BASE_DIR / "logs"


def get_daily_log_path() -> Path:
    """
    Retorna o caminho do arquivo de log diário no padrão DDMMYYYY.

    Exemplo: logs/app_audit_02032026.log
    """
    now = datetime.now()
    date_str = now.strftime("%d%m%Y")  # DDMMYYYY
    return LOG_DIR / f"app_audit_{date_str}.log"


# =========================
# Configuração do logger
# =========================

_audit_logger = None
_logger_lock = threading.Lock()


def setup_daily_logger() -> logging.Logger:
    """
    Cria e configura o logger de auditoria que grava
    diretamente no arquivo do dia atual.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("audit_daily")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    current_log = get_daily_log_path()

    # Handler simples para o arquivo do dia atual
    handler = logging.FileHandler(current_log, encoding="utf-8")

    # Formato chave=valor, fácil de parsear
    formatter = logging.Formatter(
        '%(asctime)s action=%(action)s status=%(status)s '
        'user="%(user)s" resource="%(resource)s" details="%(details)s"',
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_audit_logger() -> logging.Logger:
    """
    Retorna um singleton do logger de auditoria (thread-safe).
    """
    global _audit_logger
    if _audit_logger is None:
        with _logger_lock:
            if _audit_logger is None:
                _audit_logger = setup_daily_logger()
    return _audit_logger


# =========================
# Função pública de log
# =========================

def log_acao(
    action: str,
    user: str | None = None,
    resource=None,
    status: str = "success",
    details=None,
) -> None:
    """
    Log de auditoria em formato chave=valor, gravado em arquivos diários.

    Exemplo de linha:
    2026-03-02T12:20:30 action=login status=success user="admin" resource="CHV-001" details="Acesso normal"
    """
    try:
        logger = get_audit_logger()

        safe_resource = ""
        if resource is not None:
            safe_resource = str(resource).replace('"', "'").replace("\n", "\\n")

        safe_details = ""
        if details is not None:
            safe_details = str(details).replace('"', "'").replace("\n", "\\n")

        logger.info(
            "",
            extra={
                "action": action,
                "status": status,
                "user": user or "",
                "resource": safe_resource,
                "details": safe_details,
            },
        )
    except Exception as e:
        # Fallback: nunca deixar o app quebrar por causa de log
        ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        sys.stderr.write(f'AUDIT-ERROR {ts} action="{action}" error="{e}"\n')


# =========================
# Compatibilidade com código antigo
# =========================

# Garante que a pasta exista mesmo se usarem LOG_FILE direto
LOG_DIR.mkdir(parents=True, exist_ok=True)
# Caminho do arquivo de log atual (usado por outras partes do sistema)
LOG_FILE = get_daily_log_path()
