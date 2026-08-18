from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QMessageBox, QHeaderView, QAbstractItemView, QLabel, QComboBox,
    QSplitter, QGroupBox
)
from PyQt6.QtCore import Qt
from autenticacao.helpers_autenticacao import get_db_connection
from utils.button_style import aplicar_estilo_botao_padrao
from utils.utils_log import log_acao
from autenticacao import get_current_user


class SalaDialog(QDialog):
    def __init__(self, parent=None, sala_id=None):
        super().__init__(parent)
        self.sala_id = sala_id
        self.setWindowTitle("Editar Sala" if sala_id else "Nova Sala")
        self.setMinimumWidth(450)

        layout = QFormLayout(self)
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Ex: 210 - Gestão de Ensino")

        # Lista de Prédios
        self.combo_predio = QComboBox()
        self.combo_predio.addItem("Selecione o Prédio...", None)
        self.carregar_predios()

        # Lista de Anexos
        self.combo_anexo = QComboBox()
        self.combo_anexo.addItem("Selecione o Anexo...", None)
        self.carregar_anexos()

        self.input_descricao = QLineEdit()
        self.input_descricao.setPlaceholderText("Descrição opcional")

        layout.addRow("Nome / Código:", self.input_nome)
        layout.addRow("Prédio:", self.combo_predio)
        layout.addRow("Anexo:", self.combo_anexo)
        layout.addRow("Descrição:", self.input_descricao)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self.validar_e_salvar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

        if sala_id:
            self.carregar_dados()

    def carregar_predios(self):
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM predios ORDER BY nome")
            for pid, nome in cur.fetchall():
                self.combo_predio.addItem(str(nome), pid)
        finally:
            conn.close()

    def carregar_anexos(self):
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM anexos ORDER BY nome")
            for aid, nome in cur.fetchall():
                self.combo_anexo.addItem(str(nome), aid)
        finally:
            conn.close()

    def carregar_dados(self):
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT nome, descricao, predio_id, anexo_id FROM salas WHERE id = %s", (self.sala_id,))
            row = cur.fetchone()
            if row:
                nome, desc, predio_id, anexo_id = row
                self.input_nome.setText(str(nome or ""))
                self.input_descricao.setText(str(desc or ""))

                # Seleciona o Prédio
                for i in range(self.combo_predio.count()):
                    if self.combo_predio.itemData(i) == predio_id:
                        self.combo_predio.setCurrentIndex(i)
                        break

                # Seleciona o Anexo
                for i in range(self.combo_anexo.count()):
                    if self.combo_anexo.itemData(i) == anexo_id:
                        self.combo_anexo.setCurrentIndex(i)
                        break
        finally:
            conn.close()

    def validar_e_salvar(self):
        nome = self.input_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Aviso", "O nome/código da sala é obrigatório.")
            return
        self.accept()

    def get_dados(self):
        return {
            "nome": self.input_nome.text().strip(),
            "descricao": self.input_descricao.text().strip() or None,
            "predio_id": self.combo_predio.currentData(),
            "anexo_id": self.combo_anexo.currentData()
        }


class ChaveFisicaDialog(QDialog):
    def __init__(self, parent=None, sala_id=None, chave_id=None):
        super().__init__(parent)
        self.sala_id = sala_id
        self.chave_id = chave_id
        self.setWindowTitle("Editar Chave" if chave_id else "Nova Chave")
        self.setMinimumWidth(450)

        layout = QFormLayout(self)
        self.etiqueta = QLineEdit()
        self.etiqueta.setPlaceholderText("Ex: 210 - Gestão de Ensino")

        self.combo_sala = QComboBox()
        self.carregar_lista_salas()

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem("🔑 Principal", "principal")
        self.combo_tipo.addItem("🔒 Reserva/Cópia", "reserva")

        self.combo_status = QComboBox()
        self.combo_status.addItem("✅ Disponível", "disponivel")
        self.combo_status.addItem("⚠️ Indisponível", "indisponivel")

        layout.addRow("Etiqueta / Nome:", self.etiqueta)
        layout.addRow("🔗 Sala Vinculada:", self.combo_sala)
        layout.addRow("Tipo:", self.combo_tipo)
        layout.addRow("Status:", self.combo_status)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self.validar_e_salvar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

        if chave_id:
            self.carregar_dados()
        else:
            if self.sala_id:
                idx = self.combo_sala.findData(self.sala_id)
                if idx >= 0:
                    self.combo_sala.setCurrentIndex(idx)

    def carregar_lista_salas(self):
        self.combo_sala.clear()
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, nome, descricao FROM salas ORDER BY nome")
            for sid, nome, desc in cur.fetchall():
                texto = f"{nome}"
                if desc:
                    texto += f" - {desc}"
                self.combo_sala.addItem(texto, sid)
        finally:
            conn.close()

    def carregar_dados(self):
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT etiqueta, tipo, status, sala_id FROM chaves_fisicas WHERE id = %s",
                (self.chave_id,)
            )
            row = cur.fetchone()
            if row:
                self.etiqueta.setText(str(row[0] or ""))
                idx_tipo = self.combo_tipo.findData(row[1])
                if idx_tipo >= 0:
                    self.combo_tipo.setCurrentIndex(idx_tipo)
                idx_status = self.combo_status.findData(row[2])
                if idx_status >= 0:
                    self.combo_status.setCurrentIndex(idx_status)
                idx_sala = self.combo_sala.findData(row[3])
                if idx_sala >= 0:
                    self.combo_sala.setCurrentIndex(idx_sala)
        finally:
            conn.close()

    def validar_e_salvar(self):
        if not self.etiqueta.text().strip():
            QMessageBox.warning(self, "Aviso", "A etiqueta da chave é obrigatória.")
            return
        if self.combo_sala.currentData() is None:
            QMessageBox.warning(self, "Aviso", "Selecione uma sala para vincular.")
            return
        self.accept()

    def get_dados(self):
        return {
            "etiqueta": self.etiqueta.text().strip(),
            "tipo": self.combo_tipo.currentData(),
            "status": self.combo_status.currentData(),
            "sala_id": self.combo_sala.currentData()
        }


class SalasTab(QWidget):
    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.sala_selecionada_id = None
        self.init_ui()
        self.carregar_salas()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        grupo_salas = QGroupBox("Salas")
        layout_salas = QVBoxLayout(grupo_salas)

        botoes_salas = QHBoxLayout()
        self.btn_nova_sala = QPushButton("➕ Nova Sala")
        self.btn_editar_sala = QPushButton("✏️ Editar Sala")
        self.btn_excluir_sala = QPushButton("🗑️ Excluir Sala")
        self.btn_sincronizar = QPushButton("🔄 Sincronizar Chaves com Sala")

        for btn in [self.btn_nova_sala, self.btn_editar_sala, self.btn_excluir_sala, self.btn_sincronizar]:
            aplicar_estilo_botao_padrao(btn, cor_fundo="#007bff", cor_texto="white")
            botoes_salas.addWidget(btn)

        botoes_salas.addStretch()
        layout_salas.addLayout(botoes_salas)

        self.tabela_salas = QTableWidget()
        self.tabela_salas.setColumnCount(5)
        self.tabela_salas.setHorizontalHeaderLabels(["ID", "Nome / Código", "Descrição", "Prédio", "Anexo"])
        self.tabela_salas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_salas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela_salas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela_salas.setColumnHidden(0, True)
        self.tabela_salas.selectionModel().selectionChanged.connect(self.quando_sala_muda)
        layout_salas.addWidget(self.tabela_salas)

        grupo_chaves = QGroupBox("Chaves Físicas da Sala Selecionada")
        layout_chaves = QVBoxLayout(grupo_chaves)

        self.label_sala_atual = QLabel("Selecione uma sala acima para ver suas chaves")
        layout_chaves.addWidget(self.label_sala_atual)

        botoes_chaves = QHBoxLayout()
        self.btn_nova_chave = QPushButton("➕ Nova Chave")
        self.btn_editar_chave = QPushButton("✏️ Editar Chave / Vínculo")
        self.btn_excluir_chave = QPushButton("🗑️ Excluir Chave")

        for btn in [self.btn_nova_chave, self.btn_editar_chave, self.btn_excluir_chave]:
            aplicar_estilo_botao_padrao(btn, cor_fundo="#007bff", cor_texto="white")
            botoes_chaves.addWidget(btn)

        botoes_chaves.addStretch()
        layout_chaves.addLayout(botoes_chaves)

        self.tabela_chaves = QTableWidget()
        self.tabela_chaves.setColumnCount(5)
        self.tabela_chaves.setHorizontalHeaderLabels(["ID", "Etiqueta", "Tipo", "Status", "Ativa"])
        self.tabela_chaves.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_chaves.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela_chaves.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela_chaves.setColumnHidden(0, True)
        layout_chaves.addWidget(self.tabela_chaves)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(grupo_salas)
        splitter.addWidget(grupo_chaves)
        splitter.setSizes([300, 300])
        layout.addWidget(splitter)

        self.btn_nova_sala.clicked.connect(self.nova_sala)
        self.btn_editar_sala.clicked.connect(self.editar_sala)
        self.btn_excluir_sala.clicked.connect(self.excluir_sala)
        self.btn_sincronizar.clicked.connect(self.sincronizar_chaves)

        self.btn_nova_chave.clicked.connect(self.nova_chave)
        self.btn_editar_chave.clicked.connect(self.editar_chave)
        self.btn_excluir_chave.clicked.connect(self.excluir_chave)

        self.habilitar_botoes_chaves(False)

    def habilitar_botoes_chaves(self, sim):
        self.btn_nova_chave.setEnabled(sim)
        self.btn_editar_chave.setEnabled(sim)
        self.btn_excluir_chave.setEnabled(sim)

    def carregar_salas(self):
        self.tabela_salas.setRowCount(0)
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT s.id, s.nome, s.descricao, p.nome AS predio_nome, a.nome AS anexo_nome
                FROM salas s
                LEFT JOIN predios p ON s.predio_id = p.id
                LEFT JOIN anexos a ON s.anexo_id = a.id
                ORDER BY s.nome
            """)
            for idx, (sid, nome, desc, predio_nome, anexo_nome) in enumerate(cur.fetchall()):
                self.tabela_salas.insertRow(idx)
                self.tabela_salas.setItem(idx, 0, QTableWidgetItem(str(sid)))
                self.tabela_salas.setItem(idx, 1, QTableWidgetItem(str(nome or "")))
                self.tabela_salas.setItem(idx, 2, QTableWidgetItem(str(desc or "")))
                self.tabela_salas.setItem(idx, 3, QTableWidgetItem(str(predio_nome or "")))
                self.tabela_salas.setItem(idx, 4, QTableWidgetItem(str(anexo_nome or "")))
        finally:
            conn.close()
        self.carregar_chaves_da_sala()

    def quando_sala_muda(self):
        sel = self.tabela_salas.selectionModel().selectedRows()
        if sel:
            linha = sel[0].row()
            self.sala_selecionada_id = int(self.tabela_salas.item(linha, 0).text())
            nome = self.tabela_salas.item(linha, 1).text()
            self.label_sala_atual.setText(f"<b>Sala:</b> {nome}")
            self.habilitar_botoes_chaves(True)
            self.carregar_chaves_da_sala()
        else:
            self.sala_selecionada_id = None
            self.label_sala_atual.setText("Selecione uma sala acima para ver suas chaves")
            self.tabela_chaves.setRowCount(0)
            self.habilitar_botoes_chaves(False)

    def carregar_chaves_da_sala(self):
        self.tabela_chaves.setRowCount(0)
        if not self.sala_selecionada_id:
            return

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, etiqueta, tipo, status, ativa
                FROM chaves_fisicas
                WHERE sala_id = %s
                ORDER BY tipo = 'principal' DESC, id
            """, (self.sala_selecionada_id,))

            for idx, (cid, etiq, tipo, status, ativa) in enumerate(cur.fetchall()):
                self.tabela_chaves.insertRow(idx)
                self.tabela_chaves.setItem(idx, 0, QTableWidgetItem(str(cid)))
                self.tabela_chaves.setItem(idx, 1, QTableWidgetItem(str(etiq or "")))
                self.tabela_chaves.setItem(idx, 2, QTableWidgetItem("🔑 Principal" if tipo == "principal" else "🔒 Reserva"))
                self.tabela_chaves.setItem(idx, 3, QTableWidgetItem("✅ Disponível" if status == "disponivel" else "⚠️ Indisponível"))
                self.tabela_chaves.setItem(idx, 4, QTableWidgetItem("✅ Sim" if ativa else "❌ Não"))
        finally:
            conn.close()

    def nova_sala(self):
        dlg = SalaDialog(self)
        if dlg.exec():
            d = dlg.get_dados()
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO salas (nome, descricao, predio_id, anexo_id, status) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (d["nome"], d["descricao"], d["predio_id"], d["anexo_id"], "disponivel")
                )
                conn.commit()
                log_acao("nova_sala", get_current_user().get("login","sistema"), d["nome"], "success")
                self.carregar_salas()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Erro", f"Não foi possível salvar:\n{e}")
            finally:
                conn.close()

    def editar_sala(self):
        sel = self.tabela_salas.selectionModel().selectedRows()
        if not sel:
            return
        sid = int(self.tabela_salas.item(sel[0].row(), 0).text())
        dlg = SalaDialog(self, sala_id=sid)
        if dlg.exec():
            d = dlg.get_dados()
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE salas SET nome = %s, descricao = %s, predio_id = %s, anexo_id = %s WHERE id = %s",
                    (d["nome"], d["descricao"], d["predio_id"], d["anexo_id"], sid)
                )
                conn.commit()
                log_acao("editar_sala", get_current_user().get("login","sistema"), f"id={sid}", "success")
                self.carregar_salas()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Erro", f"Não foi possível editar:\n{e}")
            finally:
                conn.close()

    def excluir_sala(self):
        sel = self.tabela_salas.selectionModel().selectedRows()
        if not sel:
            return
        sid = int(self.tabela_salas.item(sel[0].row(), 0).text())
        nome = self.tabela_salas.item(sel[0].row(), 1).text()

        resp = QMessageBox.question(
            self, "Confirma", f"Excluir a sala:\n{nome}?\n\nATENÇÃO: Só será possível se não houver chaves vinculadas."
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM salas WHERE id = %s", (sid,))
            conn.commit()
            log_acao("excluir_sala", get_current_user().get("login","sistema"), f"{nome} (id={sid})", "success")
            self.carregar_salas()
        except Exception as e:
            conn.rollback()
            QMessageBox.warning(self, "Não excluído", f"Exclua primeiro as chaves vinculadas a esta sala.\n\nDetalhe: {e}")
        finally:
            conn.close()

    def sincronizar_chaves(self):
        if not self.sala_selecionada_id:
            QMessageBox.information(self, "Aviso", "Selecione uma sala primeiro.")
            return

        sel = self.tabela_salas.selectionModel().selectedRows()
        linha = sel[0].row()
        nome_sala = str(self.tabela_salas.item(linha, 1).text())

        resp = QMessageBox.question(
            self, "Sincronizar",
            f"Atualizar a ETIQUETA de TODAS as chaves desta sala para:\n\n{nome_sala}?"
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE chaves_fisicas
                SET etiqueta = %s, atualizada_em = CURRENT_TIMESTAMP
                WHERE sala_id = %s AND ativa = TRUE
            """, (nome_sala, self.sala_selecionada_id))
            conn.commit()
            qtd = cur.rowcount
            QMessageBox.information(self, "OK", f"{qtd} chave(s) atualizada(s)!")
            log_acao("sincronizar_chaves", get_current_user().get("login","sistema"),
                     f"sala_id={self.sala_selecionada_id}", "success", f"{qtd} chaves")
            self.carregar_chaves_da_sala()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Erro", f"Falha na sincronização:\n{e}")
        finally:
            conn.close()

    def nova_chave(self):
        if not self.sala_selecionada_id:
            return
        dlg = ChaveFisicaDialog(self, sala_id=self.sala_selecionada_id)
        if dlg.exec():
            d = dlg.get_dados()
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO chaves_fisicas (sala_id, etiqueta, tipo, status, ativa)
                    VALUES (%s, %s, %s, %s, TRUE)
                """, (d["sala_id"], d["etiqueta"], d["tipo"], d["status"]))
                conn.commit()
                log_acao("nova_chave", get_current_user().get("login","sistema"), d["etiqueta"], "success")
                self.carregar_chaves_da_sala()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Erro", f"Não foi possível criar chave:\n{e}")
            finally:
                conn.close()

    def editar_chave(self):
        sel = self.tabela_chaves.selectionModel().selectedRows()
        if not sel:
            return
        cid = int(self.tabela_chaves.item(sel[0].row(), 0).text())
        dlg = ChaveFisicaDialog(self, chave_id=cid)
        if dlg.exec():
            d = dlg.get_dados()
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE chaves_fisicas
                    SET etiqueta = %s, tipo = %s, status = %s, sala_id = %s, atualizada_em = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (d["etiqueta"], d["tipo"], d["status"], d["sala_id"], cid))
                conn.commit()
                log_acao("editar_chave/vinculo", get_current_user().get("login","sistema"), f"chave_id={cid} → sala_id={d['sala_id']}", "success")
                self.carregar_chaves_da_sala()
                self.carregar_salas()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Erro", f"Não foi possível editar:\n{e}")
            finally:
                conn.close()

    def excluir_chave(self):
        sel = self.tabela_chaves.selectionModel().selectedRows()
        if not sel:
            return
        cid = int(self.tabela_chaves.item(sel[0].row(), 0).text())
        etiq = str(self.tabela_chaves.item(sel[0].row(), 1).text())

        resp = QMessageBox.question(self, "Confirma", f"Excluir esta chave?\n{etiq}")
        if resp != QMessageBox.StandardButton.Yes:
            return

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM chaves_fisicas WHERE id = %s", (cid,))
            conn.commit()
            log_acao("excluir_chave", get_current_user().get("login","sistema"), etiq, "success")
            self.carregar_chaves_da_sala()
        except Exception as e:
            conn.rollback()
            QMessageBox.warning(self, "Não excluída", f"Esta chave está vinculada a uma movimentação em aberto.\n\n{e}")
        finally:
            conn.close()