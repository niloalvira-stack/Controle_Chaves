from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from autenticacao.helpers_autenticacao import get_db_connection
from utils.utils import montar_display_sala_por_id
from utils.button_style import aplicar_estilo_botao_padrao


class SelecionarSalaDialog(QDialog):
    def __init__(self, parent=None, is_admin=False):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Sala / Chave")
        self.setMinimumSize(1000, 580)

        self.is_admin = is_admin
        self.sala_id_selecionada = None
        self.sala_display_selecionada = None
        self.apenas_copias_reserva = False

        self.init_ui()
        self.carregar_todas_salas()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        barra_layout = QHBoxLayout()
        self.filtro_input = QLineEdit()
        self.filtro_input.setPlaceholderText("Filtrar por sala, descrição, prédio, anexo ou status")
        self.filtro_input.setMinimumHeight(32)

        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_filtrar.setMinimumWidth(90)
        aplicar_estilo_botao_padrao(self.btn_filtrar, cor_fundo="#e9ecef", cor_texto="#212529")
        self.btn_filtrar.clicked.connect(self.aplicar_filtro)
        barra_layout.addWidget(self.filtro_input)
        barra_layout.addWidget(self.btn_filtrar)
        layout.addLayout(barra_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Sala", "Descrição", "Prédio", "Anexo", "Status"])

        cabecalho = self.table.horizontalHeader()
        cabecalho.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cabecalho.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.aceitar_duplo_clique)
        layout.addWidget(self.table)

        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(12)
        botoes_layout.addStretch()

        self.btn_apenas_copias = QPushButton("Apenas Cópias/Reserva")
        self.btn_apenas_copias.setCheckable(True)
        self.btn_apenas_copias.setMinimumWidth(150)
        aplicar_estilo_botao_padrao(self.btn_apenas_copias, cor_fundo="#e9ecef", cor_texto="#212529")
        self.btn_apenas_copias.clicked.connect(self.alternar_filtro_copias)
        if not self.is_admin:
            self.btn_apenas_copias.setVisible(False)
        botoes_layout.addWidget(self.btn_apenas_copias)

        self.btn_ok = QPushButton("OK")
        self.btn_ok.setMinimumWidth(90)
        aplicar_estilo_botao_padrao(self.btn_ok, cor_fundo="#007bff", cor_texto="white")
        self.btn_ok.clicked.connect(self.validar_e_aceitar)
        botoes_layout.addWidget(self.btn_ok)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setMinimumWidth(90)
        aplicar_estilo_botao_padrao(self.btn_cancelar, cor_fundo="#6c757d", cor_texto="white")
        self.btn_cancelar.clicked.connect(self.reject)
        botoes_layout.addWidget(self.btn_cancelar)

        layout.addLayout(botoes_layout)

    def alternar_filtro_copias(self):
        self.apenas_copias_reserva = not self.apenas_copias_reserva
        self.btn_apenas_copias.setText("Mostrar Principais" if self.apenas_copias_reserva else "Apenas Cópias/Reserva")
        self.carregar_todas_salas()

    def carregar_todas_salas(self):
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            filtrar_copias = self.apenas_copias_reserva

            cur.execute("""
                SELECT DISTINCT 
                    s.id, 
                    s.nome AS sala, 
                    s.descricao, 
                    COALESCE(p.nome, '') AS predio, 
                    COALESCE(a.nome, '') AS anexo,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM movimentacoes m
                            WHERE m.sala_id = s.id
                              AND m.data_retorno IS NULL
                              AND (NOW() - m.data_retirada) > INTERVAL '24 hours'
                        ) THEN 'atraso'
                        WHEN EXISTS (
                            SELECT 1 FROM movimentacoes m
                            WHERE m.sala_id = s.id
                              AND m.data_retorno IS NULL
                        ) OR EXISTS (
                            SELECT 1 FROM chaves_fisicas cf2
                            WHERE cf2.sala_id = s.id
                              AND cf2.ativa = TRUE
                              AND cf2.status = 'retirada'
                              AND (
                                   (%s = FALSE AND cf2.tipo = 'principal')
                                   OR (%s = TRUE AND cf2.tipo IN ('copia','reserva'))
                                  )
                        ) THEN 'retirada'
                        ELSE 'disponivel'
                    END AS status
                FROM salas s
                LEFT JOIN predios p ON p.id = s.predio_id
                LEFT JOIN anexos a ON a.id = s.anexo_id
                WHERE 
                    -- ✅ Botão desmarcado: SOMENTE salas com CHAVE PRINCIPAL
                    (%s = FALSE AND EXISTS (
                        SELECT 1 FROM chaves_fisicas cf
                        WHERE cf.sala_id = s.id 
                          AND cf.ativa = TRUE 
                          AND cf.tipo = 'principal'
                    ))
                    -- ✅ Botão marcado: SOMENTE salas com CÓPIA/RESERVA
                    OR (%s = TRUE AND EXISTS (
                        SELECT 1 FROM chaves_fisicas cf
                        WHERE cf.sala_id = s.id 
                          AND cf.ativa = TRUE 
                          AND cf.tipo IN ('copia', 'reserva')
                    ))
                ORDER BY s.nome, s.descricao
            """, (filtrar_copias, filtrar_copias, filtrar_copias, filtrar_copias))

            linhas = cur.fetchall()
            self.preencher_tabela(linhas)
        finally:
            conn.close()

    def aplicar_filtro(self):
        texto = self.filtro_input.text().strip()
        if not texto:
            self.carregar_todas_salas()
            return

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            filtrar_copias = self.apenas_copias_reserva

            cur.execute("""
                SELECT DISTINCT 
                    s.id, 
                    s.nome AS sala, 
                    s.descricao, 
                    COALESCE(p.nome, '') AS predio, 
                    COALESCE(a.nome, '') AS anexo,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM movimentacoes m
                            WHERE m.sala_id = s.id
                              AND m.data_retorno IS NULL
                              AND (NOW() - m.data_retirada) > INTERVAL '24 hours'
                        ) THEN 'atraso'
                        WHEN EXISTS (
                            SELECT 1 FROM movimentacoes m
                            WHERE m.sala_id = s.id
                              AND m.data_retorno IS NULL
                        ) OR EXISTS (
                            SELECT 1 FROM chaves_fisicas cf2
                            WHERE cf2.sala_id = s.id
                              AND cf2.ativa = TRUE
                              AND cf2.status = 'retirada'
                              AND (
                                   (%s = FALSE AND cf2.tipo = 'principal')
                                   OR (%s = TRUE AND cf2.tipo IN ('copia','reserva'))
                                  )
                        ) THEN 'retirada'
                        ELSE 'disponivel'
                    END AS status
                FROM salas s
                LEFT JOIN predios p ON p.id = s.predio_id
                LEFT JOIN anexos a ON a.id = s.anexo_id
                WHERE 
                    -- ✅ Botão desmarcado: SOMENTE salas com CHAVE PRINCIPAL
                    ((%s = FALSE AND EXISTS (
                        SELECT 1 FROM chaves_fisicas cf
                        WHERE cf.sala_id = s.id 
                          AND cf.ativa = TRUE 
                          AND cf.tipo = 'principal'
                    ))
                    -- ✅ Botão marcado: SOMENTE salas com CÓPIA/RESERVA
                    OR (%s = TRUE AND EXISTS (
                        SELECT 1 FROM chaves_fisicas cf
                        WHERE cf.sala_id = s.id 
                          AND cf.ativa = TRUE 
                          AND cf.tipo IN ('copia', 'reserva')
                    )))
                    AND (s.nome ILIKE %s OR s.descricao ILIKE %s OR p.nome ILIKE %s OR a.nome ILIKE %s)
                ORDER BY s.nome
            """, (filtrar_copias, filtrar_copias, filtrar_copias, filtrar_copias,
                  f"%{texto}%", f"%{texto}%", f"%{texto}%", f"%{texto}%"))

            self.preencher_tabela(cur.fetchall())
        finally:
            conn.close()

    def preencher_tabela(self, dados):
        self.table.setRowCount(0)
        for idx, (sala_id, sala, desc, predio, anexo, status) in enumerate(dados):
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(str(sala)))
            self.table.setItem(idx, 1, QTableWidgetItem(str(desc or "")))
            self.table.setItem(idx, 2, QTableWidgetItem(str(predio or "")))
            self.table.setItem(idx, 3, QTableWidgetItem(str(anexo or "")))

            item_status = QTableWidgetItem()
            if status == "disponivel":
                item_status.setText("disponivel")
                item_status.setBackground(Qt.GlobalColor.green)
                item_status.setForeground(Qt.GlobalColor.black)
            elif status == "retirada":
                item_status.setText("indisponivel")
                item_status.setBackground(Qt.GlobalColor.yellow)
                item_status.setForeground(Qt.GlobalColor.black)
            elif status == "atraso":
                item_status.setText("em atraso")
                item_status.setBackground(Qt.GlobalColor.red)
                item_status.setForeground(Qt.GlobalColor.white)

            self.table.setItem(idx, 4, item_status)
            self.table.item(idx, 0).setData(Qt.ItemDataRole.UserRole, sala_id)

    def aceitar_duplo_clique(self):
        if self.table.currentRow() >= 0:
            self.validar_e_aceitar()

    def validar_e_aceitar(self):
        linha = self.table.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione uma sala primeiro!")
            return

        self.sala_id_selecionada = self.table.item(linha, 0).data(Qt.ItemDataRole.UserRole)
        self.sala_display_selecionada = montar_display_sala_por_id(self.sala_id_selecionada)
        self.accept()