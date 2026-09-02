# controle/__init__.py
from .movimentacoes import MovimentacoesTab, listar_movimentacoes


def __init__(self):
    super().__init__()

    # ✅ CHAMA LOGIN ANTES DE TUDO
    if not self.mostrar_login():
        return

    self.sala_id_atual = None
    # ... resto do init continua igual