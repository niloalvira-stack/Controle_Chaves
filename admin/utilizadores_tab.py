# admin/utilizadores_tab.py
import csv
import logging
from contextlib import closing

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QInputDialog, QLineEdit, QDialog,
    QFormLayout, QDialogButtonBox, QSizePolicy, QHeaderView, QFileDialog
)
from PyQt5.QtCore import Qt

from autenticacao.helpers_autenticacao import get_db_connection
from autenticacao import get_current_user, validar_login, is_admin

logger = logging.getLogger(__name__)


class UtilizadorDialog(QDialog):
    """Diálogo para cadastro/edição de utilizador."""

    def __init__(self, parent=None, dados=None, titulo="Cadastro de Utilizador"):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.resize(400, 150)

        layout = QFormLayout(self)
        self.edit_nome = QLineEdit()
        self.edit_email = QLineEdit()

        layout.addRow("Nome *:", self.edit_nome)
        layout.addRow("Email:", self.edit_email)

        if dados:
            self.edit_nome.setText(dados.get("nome", ""))
            self.edit_email.setText(dados.get("email", ""))

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_dados(self):
        return {
            "nome": self.edit_nome.text().strip(),
            "email": self.edit_email.text().strip(),
        }

    def is_valid(self):
        return bool(self.edit_nome.text().strip())


class UtilizadoresTab(QWidget):
    def __init__(self, movimentacoes_tab=None):
        super().__init__()
        self.movimentacoes_tab = movimentacoes_tab
        self.setup_ui()
        self.setup_connections()
        self.load_utilizadores()

    def setup_ui(self):
        """Configura a interface do usuário."""
        self.setWindowTitle("Gestão de Utilizadores")
        self.resize(800, 500)

        layout = QVBoxLayout(self)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Email", "Ativo"])
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID fixo
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Nome
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Email
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Ativo

        # Botões
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Adicionar")
        self.btn_toggle = QPushButton("🔄 Ativar/Desativar")
        self.btn_delete = QPushButton("🗑️ Excluir")
        self.btn_export = QPushButton("📊 Exportar CSV")

        for btn in (self.btn_add, self.btn_toggle, self.btn_delete, self.btn_export):
            btn_layout.addWidget(btn)

        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def setup_connections(self):
        """Conecta sinais aos slots."""
        self.btn_add.clicked.connect(self.adicionar_utilizador)
        self.btn_toggle.clicked.connect(self.desativar_reativar_utilizador)
        self.btn_delete.clicked.connect(self.excluir_utilizador)
        self.btn_export.clicked.connect(self.exportar_csv)

    def _get_dash_main(self):
        """Encontra DashMain na hierarquia de parents."""
        widget = self.parentWidget()
        while widget and widget.__class__.__name__ != "DashMain":
            widget = widget.parentWidget()
        return widget

    def show_success(self, mensagem):
        """Exibe mensagem de sucesso via DashMain ou QMessageBox."""
        dash = self._get_dash_main()
        if dash:
            dash.show_operation_done(mensagem)
        else:
            QMessageBox.information(self, "Sucesso", mensagem)

    def _get_selected_user(self):
        """Retorna (id, nome) do utilizador selecionado ou None."""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Atenção", "Selecione um utilizador!")
            return None

        row = selected[0].row()
        try:
            util_id = int(self.table.item(row, 0).text())
            nome = self.table.item(row, 1).text()
            return util_id, nome
        except (ValueError, AttributeError):
            QMessageBox.warning(self, "Erro", "Dados inválidos na seleção!")
            return None

    def load_utilizadores(self):
        """Carrega utilizadores da base de dados."""
        try:
            with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:
                cur.execute(
                    "SELECT id, nome, email, ativo FROM utilizadores ORDER BY nome"
                )
                rows = cur.fetchall()

            self.table.setRowCount(len(rows))
            for r, (uid, nome, email, ativo) in enumerate(rows):
                self.table.setItem(r, 0, QTableWidgetItem(str(uid)))
                self.table.setItem(r, 1, QTableWidgetItem(nome or ""))
                self.table.setItem(r, 2, QTableWidgetItem(email or ""))
                self.table.setItem(r, 3, QTableWidgetItem("✅" if ativo else "❌"))

            logger.info(f"Carregados {len(rows)} utilizadores")
        except Exception as e:
            logger.error(f"Erro ao carregar utilizadores: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados: {e}")

    def adicionar_utilizador(self):
        """Adiciona novo utilizador."""
        dialog = UtilizadorDialog(self)
        if dialog.exec() != dialog.Accepted or not dialog.is_valid():
            return

        dados = dialog.get_dados()
        try:
            with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:
                cur.execute(
                    "INSERT INTO utilizadores (nome, email, ativo) VALUES (%s, %s, %s)",
                    (dados["nome"], dados["email"], True)
                )
                conn.commit()

            self.load_utilizadores()
            self._atualizar_combo_movimentacoes()
            self.show_success("Utilizador criado com sucesso!")

        except Exception as e:
            logger.error(f"Erro ao adicionar utilizador: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao criar utilizador: {e}")

    def desativar_reativar_utilizador(self):
        """Alterna status ativo/inativo."""
        user_data = self._get_selected_user()
        if not user_data:
            return

        util_id, nome = user_data
        row = self.table.currentRow()
        status_atual = self.table.item(row, 3).text() == "✅"
        novo_status = not status_atual  # True / False

        try:
            with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:
                cur.execute(
                    "UPDATE utilizadores SET ativo = %s WHERE id = %s",
                    (novo_status, util_id)
                )
                conn.commit()

            self.load_utilizadores()
            self._atualizar_combo_movimentacoes()
            status_texto = "ativado" if novo_status else "desativado"
            self.show_success(f"Utilizador '{nome}' {status_texto}")

        except Exception as e:
            logger.error(f"Erro ao alterar status: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao alterar status: {e}")

    def excluir_utilizador(self):
        """Exclui utilizador com validações."""
        user_data = self._get_selected_user()
        if not user_data:
            return

        util_id, nome = user_data

        # Verifica movimentações
        try:
            with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM movimentacoes 
                    WHERE utilizador_id = %s OR usuario = %s
                    """,
                    (util_id, nome)
                )
                qtd = cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Erro ao verificar movimentações: {e}")
            return

        if qtd > 0:
            QMessageBox.warning(
                self, "Não permitido",
                "Este utilizador possui movimentações associadas.\n"
                "Use apenas 'Ativar/Desativar'."
            )
            return

        # Validação de senha para não-admins
        if not is_admin():
            user = get_current_user()
            if not user:
                QMessageBox.warning(self, "Erro", "Nenhum usuário logado.")
                return

            senha, ok = QInputDialog.getText(
                self, "🔐 Confirmação de Senha",
                f"Digite sua senha para excluir '{nome}':",
                QLineEdit.Password
            )
            if not ok or not validar_login(user["login"], senha):
                QMessageBox.warning(self, "Acesso Negado", "Senha inválida!")
                return

        # Confirmação final
        resp = QMessageBox.question(
            self, "⚠️ Confirmar Exclusão",
            f"Excluir permanentemente o utilizador '{nome}'?\n\n"
            "Esta ação não pode ser desfeita!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if resp != QMessageBox.Yes:
            return

        try:
            with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:
                cur.execute("DELETE FROM utilizadores WHERE id = %s", (util_id,))
                conn.commit()

            self.load_utilizadores()
            self._atualizar_combo_movimentacoes()
            self.show_success("Utilizador excluído permanentemente!")

        except Exception as e:
            logger.error(f"Erro ao excluir utilizador: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao excluir: {e}")

    def exportar_csv(self):
        """Exporta tabela para CSV."""
        path, _ = QFileDialog.getSaveFileName(
            self, "📊 Exportar Utilizadores",
            "utilizadores.csv",
            "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                # Headers
                headers = [self.table.horizontalHeaderItem(c).text()
                           for c in range(self.table.columnCount())]
                writer.writerow(headers)

                # Dados
                for row in range(self.table.rowCount()):
                    linha = [self.table.item(row, col).text()
                             if self.table.item(row, col) else ""
                             for col in range(self.table.columnCount())]
                    writer.writerow(linha)

            self.show_success(f"Exportado para: {path}")
            logger.info(f"CSV exportado: {path}")

        except Exception as e:
            logger.error(f"Erro no export CSV: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar: {e}")

    def _atualizar_combo_movimentacoes(self):
        """Atualiza combo de utilizadores na aba de movimentações."""
        if self.movimentacoes_tab:
            try:
                self.movimentacoes_tab.load_utilizadores_combo()
            except Exception as e:
                logger.warning(f"Falha ao atualizar combo: {e}")
