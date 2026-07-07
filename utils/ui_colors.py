# utils/ui_colors.py
import logging
logger = logging.getLogger(__name__)

from datetime import datetime
from PyQt6.QtGui import QBrush, QColor
import config

ALERTA_HORAS = 6


def _parse_datetime_safe(valor):
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor
    try:
        return datetime.strptime(str(valor), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def aplicar_cor_status_item_generico(item, status, retirada_val, retorno_val=None, now=None):
    status_original = status
    status = (status or "").strip().lower()
    now = now or datetime.now()

    # Normalização de problemas de encoding/acento
    if status in ("dispon¡vel", "disponivel", "disponível"):
        status = "disponivel"
    elif status in ("indispon¡vel", "indisponivel", "indisponível"):
        status = "indisponivel"

    logger.debug(
        f"[COR] status_original={status_original!r} status_norm={status!r} "
        f"retirada={retirada_val!r} retorno={retorno_val!r} now={now}"
    )

    try:
        if retorno_val:
            cor_hex = config.COLOR_STATUS_DISPONIVEL
        else:
            if status == "disponivel":
                cor_hex = config.COLOR_STATUS_DISPONIVEL
            elif status == "indisponivel":
                retirada_dt = _parse_datetime_safe(retirada_val)
                atraso = False
                if retirada_dt:
                    diff_horas = (now - retirada_dt).total_seconds() / 3600.0
                    atraso = diff_horas >= ALERTA_HORAS

                cor_hex = (
                    config.COLOR_STATUS_ATRASO
                    if atraso
                    else config.COLOR_STATUS_INDISPONIVEL
                )
            else:
                return

        item.setBackground(QBrush(QColor(cor_hex)))
    except Exception as e:
        logger.error(f"[COR] erro ao aplicar cor: {e}")
        pass
