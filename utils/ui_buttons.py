import logging
logger = logging.getLogger(__name__)

from PyQt6.QtWidgets import QPushButton


def aplicar_estilo_botao_padrao(botao: QPushButton, role="primary", altura=35, largura_min=100):
    """
    Aplica o padrão visual de botões do sistema sem sobrescrever o QSS global.
    Use roles para o stylesheet principal decidir cor e aparência.
    """
    try:
        botao.setProperty("role", role)

        if altura:
            botao.setFixedHeight(altura)

        if largura_min:
            botao.setMinimumWidth(largura_min)

        botao.style().unpolish(botao)
        botao.style().polish(botao)
        botao.update()

    except Exception as e:
        logger.error(f"Erro ao aplicar estilo padrão no botão {botao}: {e}")


def criar_botao_padrao(texto, role="primary", altura=35, largura_min=100, slot=None):
    btn = QPushButton(texto)
    aplicar_estilo_botao_padrao(btn, role=role, altura=altura, largura_min=largura_min)

    if slot is not None:
        btn.clicked.connect(slot)

    return btn