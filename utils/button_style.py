from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QColor


def aplicar_estilo_botao_padrao(
    botao,
    cor_fundo,
    cor_texto,
    cor_hover=None,
    cor_pressed=None,
    fixa_altura_35=True,
):
    """
    Aplica o estilo padrão de botão usado em todo o sistema.
    Se não informadas, as cores de hover e clique são geradas automaticamente.
    """
    # Gera cor de hover mais escura se não for informada
    if cor_hover is None:
        cor = QColor(cor_fundo)
        cor_hover = cor.darker(110).name()  # 10% mais escuro

    # Gera cor de pressionado ainda mais escura
    if cor_pressed is None:
        cor = QColor(cor_fundo)
        cor_pressed = cor.darker(120).name()  # 20% mais escuro

    estilo = f"""
        QPushButton {{
            background-color: {cor_fundo};
            color: {cor_texto};
            border: none;
            border-radius: 6px;
            padding: 6px 14px;
            min-width: 100px;
            min-height: 35px;
            font-size: 13px;
            text-align: center;
        }}
        QPushButton:hover {{
            background-color: {cor_hover};
        }}
        QPushButton:pressed {{
            background-color: {cor_pressed};
        }}
        QPushButton:disabled {{
            background-color: #adb5bd;
            color: #f8f9fa;
        }}
    """
    botao.setStyleSheet(estilo)

    if fixa_altura_35:
        botao.setFixedHeight(35)