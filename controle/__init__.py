def __init__(self, dash_main_ref=None):
    super().__init__()
    self.dash_main_ref = dash_main_ref
    self.sala_id_atual = None
    self.filtro_atual = None
    self.chave_fisica_id_atual = None
    self._em_operacao = False
    self.filtro_apenas_copias = False

    # ✅ Pega direto do painel principal (já está correto)
    if self.dash_main_ref and hasattr(self.dash_main_ref, 'eh_admin'):
        self.eh_admin = self.dash_main_ref.eh_admin
    else:
        # Fallback se não vier a referência
        self.utilizador_atual = get_current_user()
        self.eh_admin = False
        if self.utilizador_atual:
            if hasattr(self.utilizador_atual, "is_admin"):
                self.eh_admin = bool(self.utilizador_atual.is_admin)
            elif isinstance(self.utilizador_atual, dict):
                self.eh_admin = bool(self.utilizador_atual.get("is_admin", False))

    print(f"🔍 MOV — eh_admin = {self.eh_admin}")

    self.label_atraso = None
    self.init_ui()

    # Restante continua igual...