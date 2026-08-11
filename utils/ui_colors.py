import logging
from PyQt6.QtGui import QBrush, QColor

logger = logging.getLogger(__name__)

def _normalizar_status(status):
    if not status:
        return ""
    s = str(status).strip().lower()
    if s in ("disponível", "disponivel"):
        return "disponivel"
    if s in ("indisponível", "indisponivel"):
        return "indisponivel"
    return s

def aplicar_cor_status_item_generico(item, status, data_retirada=None, data_devolucao=None, agora=None):
    status = _normalizar_status(status)

    if status == "disponivel":
        item.setBackground(QBrush(QColor("#d4edda")))
        item.setForeground(QBrush(QColor("#155724")))
    elif status == "indisponivel":
        item.setBackground(QBrush(QColor("#fff3cd")))
        item.setForeground(QBrush(QColor("#856404")))
    else:
        item.setBackground(QBrush(QColor("#f8f9fa")))
        item.setForeground(QBrush(QColor("#212529")))