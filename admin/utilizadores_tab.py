# admin/utilizadores_tab.py
import csv
from contextlib import closing

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QInputDialog, QLineEdit, QDialog,
    QFormLayout, QDialogButtonBox, QSizePolicy, QHeaderView, QFileDialog
)

from autenticacao.helpers_autenticacao import (
    get_db_connection, get_current_user, validar_login, is_admin
)


class UtilizadorDialog(QDialog):
    """
    Diálogo simples para cadastro de utilizador.
    Trabalha com a tabela `utilizadores` (nome, email).
    """
    def __init__(self, parent=None, dados=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastro de Utilizador")

        layout = QFormLayout(self)

        self.edit_nome = QLineEdit()
        self.edit_email = QLineEdit()

        layout.addRow("Nome:", self.edit_nome)
        layout.addRow("Email:", self.edit_email)

        if dados:
            self.edit_nome.setText(dados.get("nome", ""))
            self.edit_email.setText(dados.get("email", ""))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_dados(self):
        return {
            "nome": self.edit_nome.text().strip(),
            "email": self.edit_email.text().strip(),
        }


class UtilizadoresTab(QWidget):
    def __init__(self, movimentacoes_tab=None):
        """
        movimentacoes_tab: referência opcional para MovimentacoesTab,
        usada para recarregar o combo de utilizadores após ativar/desativar.
        """
        super().__init__()
        self.movimentacoes_tab = movimentacoes_tab

        self.setWindowTitle("Gestão de Utilizadores")
        self.resize(700, 400)

        self.layout = QVBoxLayout(self)

        # Tabela de utilizadores: id, nome, email, ativo
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Email", "Ativo"])
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.SingleSelection)

        # Faz a tabela ocupar todo o espaço disponível
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Barra de botões (sem Editar)
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton("Adicionar")
        self.btn_toggle = QPushButton("Desativar / Reativar")
        self.btn_delete = QPushButton("Excluir")
        self.btn_export = QPushButton("Exportar CSV")

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_toggle)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_export)

        self.layout.addWidget(self.table)
        self.layout.addLayout(btn_layout)

        # Conexões de sinais
        self.btn_add.clicked.connect(self.adicionar_utilizador)
        self.btn_toggle.clicked.connect(self.desativar_reativar_utilizador)
        self.btn_delete.clicked.connect(self.excluir_utilizador)
        self.btn_export.clicked.connect(self.exportar_csv)

        self.load_utilizadores()

    # ========= Utilitário para acessar DashMain ==========
    def _get_dash_main(self):
        """
        Sobe na hierarquia de parents até encontrar a janela principal (DashMain),
        para poder chamar show_operation_done.
        """
        from interface.dash_main import DashMain  # import local para evitar ciclos

        janela = self.parentWidget()
        while janela is not None and not isinstance(janela, DashMain):
            janela = janela.parentWidget()
        return janela

    # ========= Exportar CSV ==========
    def exportar_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Utilizadores",
            "",
            "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                headers = [
                    self.table.horizontalHeaderItem(c).text()
                    for c in range(self.table.columnCount())
                ]
                writer.writerow(headers)

                for row in range(self.table.rowCount()):
                    linha = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        linha.append(item.text() if item else "")
                    writer.writerow(linha)

            QMessageBox.information(self, "Exportação", "Exportação concluída!")
            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Exportação concluída")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV: {e}")

    # ========= Carregar dados ==========
    def load_utilizadores(self):
        with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:
            cur.execute(
                """
                SELECT id, nome, email, ativo
                FROM utilizadores
                ORDER BY nome
                """
            )
            rows = cur.fetchall()

        self.table.setRowCount(len(rows))
        for r, (uid, nome, email, ativo) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(uid)))
            self.table.setItem(r, 1, QTableWidgetItem(str(nome)))
            self.table.setItem(r, 2, QTableWidgetItem(str(email) if email else ""))
            self.table.setItem(r, 3, QTableWidgetItem("Sim" if ativo else "Não"))

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

    # ========= Adicionar ==========
    def adicionar_utilizador(self):
        dialog = UtilizadorDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            dados = dialog.get_dados()
            if not dados["nome"]:
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Preencha pelo menos o nome do utilizador."
                )
                return
            try:
                with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:
                    cur.execute(
                        """
                        INSERT INTO utilizadores (nome, email, ativo)
                        VALUES (?, ?, 1)
                        """,
                        (dados["nome"], dados["email"]),
                    )
                    conn.commit()
                QMessageBox.information(
                    self,
                    "Sucesso",
                    "Utilizador criado com sucesso."
                )
                self.load_utilizadores()
                self._atualizar_combo_movimentacoes()

                dash = self._get_dash_main()
                if dash is not None:
                    dash.show_operation_done("Utilizador criado")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Erro ao criar utilizador: {e}"
                )

    # ========= Desativar / Reativar ==========
    def desativar_reativar_utilizador(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Atenção", "Selecione um utilizador!")
            return

        row = selected[0].row()
        util_id = int(self.table.item(row, 0).text())
        status_atual = self.table.item(row, 3).text() == "Sim"
        novo_status = not status_atual

        with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:
            cur.execute(
                "UPDATE utilizadores SET ativo = ? WHERE id = ?",
                (1 if novo_status else 0, util_id),
            )
            conn.commit()

        self.load_utilizadores()
        QMessageBox.information(
            self,
            "Status",
            "Utilizador ativado." if novo_status else "Utilizador desativado.",
        )
        self._atualizar_combo_movimentacoes()

        dash = self._get_dash_main()
        if dash is not None:
            msg = "Utilizador ativado" if novo_status else "Utilizador desativado"
            dash.show_operation_done(msg)

    # ========= Exclusão com checagem de movimentações + senha ==========
    def excluir_utilizador(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(
                self,
                "Atenção",
                "Selecione um utilizador para excluir!"
            )
            return

        row = selected[0].row()
        util_id = int(self.table.item(row, 0).text())
        nome = self.table.item(row, 1).text()

        with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM movimentacoes
                WHERE utilizador_id = ? OR usuario = ?
                """,
                (util_id, nome),
            )
            qtd, = cur.fetchone()

        if qtd > 0:
            QMessageBox.warning(
                self,
                "Não permitido",
                "Este utilizador possui movimentações e não pode ser excluído.\n"
                "Use apenas desativar.",
            )
            return

        user = get_current_user()
        if not user:
            QMessageBox.warning(self, "Erro", "Nenhum usuário logado.")
            return

        if not is_admin():
            senha, ok = QInputDialog.getText(
                self,
                "Confirmação necessária",
                f"Digite a sua senha para excluir o utilizador '{nome}':",
                QLineEdit.Password,
            )
            if not ok:
                return

            if not validar_login(user["login"], senha):
                QMessageBox.warning(
                    self,
                    "Senha incorreta",
                    "Senha inválida. Operação cancelada."
                )
                return

        resp = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Excluir permanentemente o utilizador '{nome}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return

        try:
            with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:
                cur.execute("DELETE FROM utilizadores WHERE id = ?", (util_id,))
                conn.commit()
            self.load_utilizadores()
            self._atualizar_combo_movimentacoes()
            QMessageBox.information(
                self,
                "Excluir Utilizador",
                "Utilizador excluído com sucesso!"
            )

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Utilizador excluído")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao excluir utilizador: {e}"
            )

    # ========= Integração com MovimentacoesTab ==========
    def _atualizar_combo_movimentacoes(self):
        """
        Se a MovimentacoesTab foi passada no construtor,
        força recarregar o combo de utilizadores (apenas ativos).
        """
        if self.movimentacoes_tab is not None:
            try:
                self.movimentacoes_tab.load_utilizadores_combo()
            except Exception as e:
                print(f"Erro ao atualizar combo de utilizadores na MovimentacoesTab: {e}")
