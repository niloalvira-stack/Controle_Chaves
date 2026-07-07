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
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


BASE_DIR = Path(get_base_dir())
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _today_str() -> str:
    return datetime.now().strftime("%d%m%Y")


def get_daily_audit_log_path() -> Path:
    return LOG_DIR / f"app_audit_{_today_str()}.log"


def get_legacy_audit_log_path() -> Path:
    return LOG_DIR / "app_audit.log"


def get_daily_app_log_path() -> Path:
    return LOG_DIR / f"app_{_today_str()}.log"


# Compatibilidade com código antigo
LOG_FILE = get_daily_audit_log_path()
TECHNICAL_LOG_FILE = get_daily_app_log_path()


# =========================
# Estado interno
# =========================

_audit_logger = None
_app_logger = None
_logger_lock = threading.Lock()
_startup_audit_registered = False


# =========================
# Helpers
# =========================

class SafeExtraFormatter(logging.Formatter):
    """
    Garante que campos extras existam mesmo quando não forem informados.
    """
    def format(self, record):
        for field in ("action", "status", "user", "resource", "details"):
            if not hasattr(record, field):
                setattr(record, field, "")
        return super().format(record)


def _sanitize(value) -> str:
    if value is None:
        return ""
    return str(value).replace('"', "'").replace("\n", "\\n")


# =========================
# Logger de auditoria
# =========================

def setup_audit_logger() -> logging.Logger:
    logger = logging.getLogger("audit_daily")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    audit_path = get_daily_audit_log_path()
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(audit_path, encoding="utf-8")
    formatter = SafeExtraFormatter(
        '%(asctime)s level=%(levelname)s logger=%(name)s '
        'action=%(action)s status=%(status)s '
        'user="%(user)s" resource="%(resource)s" details="%(details)s"',
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_audit_logger() -> logging.Logger:
    global _audit_logger
    if _audit_logger is None:
        with _logger_lock:
            if _audit_logger is None:
                _audit_logger = setup_audit_logger()
    return _audit_logger


def log_acao(
    action: str,
    user: str | None = None,
    resource=None,
    status: str = "success",
    details=None,
) -> None:
    """
    Log de auditoria para ações de usuário.
    """
    try:
        logger = get_audit_logger()
        logger.info(
            "",
            extra={
                "action": _sanitize(action),
                "status": _sanitize(status),
                "user": _sanitize(user),
                "resource": _sanitize(resource),
                "details": _sanitize(details),
            },
        )

        for handler in logger.handlers:
            try:
                handler.flush()
            except Exception:
                pass

    except Exception as e:
        ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        sys.stderr.write(f'AUDIT-ERROR {ts} action="{action}" error="{e}"\n')


def registrar_inicio_sistema() -> None:
    global _startup_audit_registered
    if _startup_audit_registered:
        return

    with _logger_lock:
        if _startup_audit_registered:
            return

        log_acao(
            action="Inicialização do sistema",
            user="system",
            resource="aplicacao",
            status="success",
            details=f"base_dir={BASE_DIR}",
        )
        _startup_audit_registered = True


# =========================
# Logger técnico da aplicação
# =========================

def setup_app_logger() -> logging.Logger:
    logger = logging.getLogger("app_daily")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    app_path = get_daily_app_log_path()
    app_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(app_path, encoding="utf-8")
    formatter = SafeExtraFormatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(module)s | '
        '%(funcName)s:%(lineno)d | %(message)s',
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_app_logger() -> logging.Logger:
    global _app_logger
    if _app_logger is None:
        with _logger_lock:
            if _app_logger is None:
                _app_logger = setup_app_logger()
    return _app_logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Retorna um logger filho do logger técnico principal.

    Uso:
        logger = get_logger(__name__)
        logger.info("Tela carregada")
        logger.exception("Erro ao salvar")
    """
    base_logger = get_app_logger()

    if not name:
        return base_logger

    logger = logging.getLogger(f"app_daily.{name}")
    logger.setLevel(logging.INFO)
    logger.propagate = True
    return logger


# Inicializa os arquivos/logo no carregamento do módulo
get_app_logger()
get_audit_logger()
registrar_inicio_sistema()