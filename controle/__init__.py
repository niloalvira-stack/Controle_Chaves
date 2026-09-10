def __init__(self, dash_main_ref=None):  # ✅ ACEITA o parâmetro!
    super().__init__()
    self.dash_main_ref = dash_main_ref  # ✅ GUARDA a referência
    self.sala_id_atual = None
    self.filtro_atual = None
    self.chave_fisica_id_atual = None
    self._em_operacao = False
    self.filtro_apenas_copias = False
    self.utilizador_atual = get_current_user()
    self.eh_admin = bool(self.utilizador_atual and self.utilizador_atual.get("is_admin"))
    self.label_atraso = None

    # ✅ SÓ CRIA A INTERFACE — sem carregar nada automaticamente
    self.init_ui()

    # ✅ Só mantém o contador de atraso
    self.timer = QTimer(self)
    self.timer.timeout.connect(self._atualizar_contagem_pendencias)
    self.timer.start(30000)
    self._atualizar_contagem_pendencias()