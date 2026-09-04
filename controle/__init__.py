def __init__(self):
    super().__init__()
    self.sala_id_atual = None
    self.filtro_atual = None
    self.chave_fisica_id_atual = None
    self._em_operacao = False
    self.filtro_apenas_copias = False
    self.utilizador_atual = get_current_user()
    self.eh_admin = bool(self.utilizador_atual and self.utilizador_atual.get("is_admin"))

    # ✅ PRIMEIRO cria TODA a interface (incluindo o rótulo de atraso)
    self.init_ui()

    # ✅ Cria o rótulo de aviso de chaves em atraso
    self.label_atraso = QLabel("")
    self.label_atraso.setStyleSheet("color: red; font-weight: bold; font-size: 11pt;")
    self.label_atraso.setVisible(False)
    # ⚠️ IMPORTANTE: No método init_ui(), adicione este widget ao layout dos botões!
    # Exemplo: layout_botoes.addWidget(self.label_atraso)

    # ✅ DEPOIS carrega os dados e inicia o timer
    try:
        self.carregar_movimentacoes()
    except Exception as e:
        QMessageBox.critical(self, "Erro", f"Falha ao carregar:\n{e}")

    # ✅ Timer para atualizar contagem a cada 5 segundos
    self.timer = QTimer(self)
    self.timer.timeout.connect(self._atualizar_contagem_pendencias)
    self.timer.start(5000)

    # ✅ Atualiza contagem IMEDIATAMENTE ao abrir a tela
    self._atualizar_contagem_pendencias()