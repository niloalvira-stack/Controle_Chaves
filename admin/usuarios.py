from PyQt6.QtWidgets import (
    QPushButton, QHBoxLayout, QVBoxLayout, QTableWidget, QMessageBox, QWidget,
    QHeaderView, QFileDialog, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QComboBox
)
from PyQt6.QtCore import Qt
from database_module import get_connection
from utils.utils_log import get_logger
from utils import button_style
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import csv
import bcrypt

logger = get_logger(__name__)


class UsuarioDialog(QDialog):
    def __init__(self, login="", nome="", is_admin=False, primeiro_login=True, parent=None, editar=False):
        super().__init__(parent)
        self.setWindowTitle("Cadastro / Edição de Usuário")
        self.setModal(True)
        self.editando = editar

        layout = QFormLayout(self)

        self.login_edit = QLineEdit(login)
        self.nome_edit = QLineEdit(nome)

        self.senha_edit = QLineEdit()
        self.senha_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.confirmar_senha_edit = QLineEdit()
        self.confirmar_senha_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.admin_combo = QComboBox()
        self.admin_combo.addItem("Não", False)
        self.admin_combo.addItem("Sim", True)
        self.admin_combo.setCurrentIndex(1 if is_admin else 0)

        self.primeiro_login_combo = QComboBox()
        self.primeiro_login_combo.addItem("Sim", True)
        self.primeiro_login_combo.addItem("Não", False)
        self.primeiro_login_combo.setCurrentIndex(0 if primeiro_login else 1)

        layout.addRow("Login:", self.login_edit)
        layout.addRow("Nome:", self.nome_edit)
        layout.addRow("Senha:", self.senha_edit)
        layout.addRow("Confirmar senha:", self.confirmar_senha_edit)
        layout.addRow("É admin?", self.admin_combo)
        layout.addRow("1º login?", self.primeiro_login_combo)

        if self.editando:
            self.senha_edit.setPlaceholderText("Preencha apenas para alterar")
            self.confirmar_senha_edit.setPlaceholderText("Preencha apenas para alterar")

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def get_data(self):
        return {
            "login": self.login_edit.text().strip(),
            "nome": self.nome_edit.text().strip(),
            "senha": self.senha_edit.text(),
            "confirmar_senha": self.confirmar_senha_edit.text(),
            "is_admin": self.admin_combo.currentData(),
            "primeiro_login": self.primeiro_login_combo.currentData()
        }


class UsuariosTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Login", "Nome", "É Admin?", "1º Login?"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setColumnHidden(0, True)

        self.btn_add = QPushButton("Novo Usuário")
        self.btn_add.clicked.connect(self.add_user)

        self.btn_edit = QPushButton("Editar Usuário")
        self.btn_edit.clicked.connect(self.edit_user)

        self.btn_delete = QPushButton("Excluir Usuário")
        self.btn_delete.clicked.connect(self.delete_user)

        self.btn_export_csv = QPushButton("Exportar CSV")
        self.btn_export_csv.clicked.connect(self.export_csv)

        self.btn_export_pdf = QPushButton("Exportar PDF")
        self.btn_export_pdf.clicked.connect(self.export_pdf)

        self._apply_button_style(self.btn_add, "primary")
        self._apply_button_style(self.btn_edit, "primary")
        self._apply_button_style(self.btn_delete, "danger")
        self._apply_button_style(self.btn_export_csv, "secondary")
        self._apply_button_style(self.btn_export_pdf, "secondary")

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.btn_add)
        hlayout.addWidget(self.btn_edit)
        hlayout.addWidget(self.btn_delete)
        hlayout.addWidget(self.btn_export_csv)
        hlayout.addWidget(self.btn_export_pdf)

        self.layout.addWidget(self.table)
        self.layout.addLayout(hlayout)

        self.load_users()

    def _apply_button_style(self, botao, estilo):
        temas = {
            "primary": ("#0d6efd", "#ffffff", "#0b5ed7", "#0a58ca"),
            "danger": ("#dc3545", "#ffffff", "#bb2d3b", "#b02a37"),
            "secondary": ("#6c757d", "#ffffff", "#5c636a", "#565e64"),
            "success": ("#198754", "#ffffff", "#157347", "#146c43"),
        }
        cor_fundo, cor_texto, cor_hover, cor_pressed = temas.get(
            estilo,
            temas["primary"]
        )
        button_style.aplicar_estilo_botao_padrao(
            botao,
            cor_fundo,
            cor_texto,
            cor_hover,
            cor_pressed
        )

    def _show_success(self, message):
        QMessageBox.information(self, "Sucesso", message)

    def _show_error(self, message):
        QMessageBox.critical(self, "Erro", message)

    def _get_selected_user_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None

        item = self.table.item(row, 0)
        if not item:
            return None

        try:
            return int(item.text())
        except ValueError:
            return None

    def _fetch_scalar(self, cursor):
        result = cursor.fetchone()
        if result is None:
            return None
        if hasattr(result, "keys"):
            return list(result.values())[0]
        return result[0]

    def load_users(self):
        conn = get_connection()
        if not conn:
            self._show_error("Falha ao conectar ao banco de dados.")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, login, nome, is_admin, primeiro_login FROM usuarios ORDER BY nome, login")
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                if hasattr(row, "keys"):
                    user_id = row.get("id")
                    login = row.get("login", "")
                    nome = row.get("nome", "")
                    is_admin_flag = row.get("is_admin", False)
                    primeiro_login_flag = row.get("primeiro_login", False)
                else:
                    user_id, login, nome, is_admin_flag, primeiro_login_flag = row

                self.table.setItem(i, 0, QTableWidgetItem(str(user_id)))
                self.table.setItem(i, 1, QTableWidgetItem(str(login or "")))
                self.table.setItem(i, 2, QTableWidgetItem(str(nome or "")))
                self.table.setItem(i, 3, QTableWidgetItem("Sim" if bool(is_admin_flag) else "Não"))
                self.table.setItem(i, 4, QTableWidgetItem("Sim" if bool(primeiro_login_flag) else "Não"))

                for col in range(5):
                    item = self.table.item(i, col)
                    if item:
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        except Exception as e:
            logger.exception("Erro ao carregar usuários")
            self._show_error(f"Erro ao carregar usuários: {e}")
        finally:
            cursor.close()
            conn.close()

    def add_user(self):
        dialog = UsuarioDialog(parent=self, editar=False)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        if not data["login"]:
            self._show_error("O login é obrigatório.")
            return

        if not data["nome"]:
            self._show_error("O nome é obrigatório.")
            return

        if not data["senha"]:
            self._show_error("A senha é obrigatória.")
            return

        if data["senha"] != data["confirmar_senha"]:
            self._show_error("A confirmação da senha não confere.")
            return

        senha_hash = bcrypt.hashpw(
            data["senha"].encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        conn = get_connection()
        if not conn:
            self._show_error("Falha ao conectar ao banco de dados.")
            return

        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO usuarios (login, nome, senha, is_admin, primeiro_login)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (login) DO NOTHING
                RETURNING id
                """,
                (
                    data["login"],
                    data["nome"],
                    senha_hash,
                    bool(data["is_admin"]),
                    bool(data["primeiro_login"]),
                )
            )

            resultado = cursor.fetchone()
            if resultado is None:
                conn.rollback()
                self._show_error("Já existe um usuário com este login.")
                return

            conn.commit()
            self.load_users()
            self._show_success("Usuário cadastrado com sucesso.")

        except Exception as e:
            conn.rollback()
            logger.exception("Erro ao cadastrar usuário")
            self._show_error(f"Erro ao cadastrar usuário: {e}")

        finally:
            cursor.close()
            conn.close()

    def edit_user(self):
        row = self.table.currentRow()
        if row < 0:
            self._show_error("Selecione um usuário para editar.")
            return

        user_id = self._get_selected_user_id()
        if user_id is None:
            self._show_error("Usuário inválido.")
            return

        login = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
        nome = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
        is_admin = (self.table.item(row, 3).text() == "Sim") if self.table.item(row, 3) else False
        primeiro_login = (self.table.item(row, 4).text() == "Sim") if self.table.item(row, 4) else True

        dialog = UsuarioDialog(
            login=login,
            nome=nome,
            is_admin=is_admin,
            primeiro_login=primeiro_login,
            parent=self,
            editar=True
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        if not data["login"]:
            self._show_error("O login é obrigatório.")
            return

        if not data["nome"]:
            self._show_error("O nome é obrigatório.")
            return

        senha_hash = None
        if data["senha"] or data["confirmar_senha"]:
            if not data["senha"]:
                self._show_error("Informe a nova senha.")
                return
            if not data["confirmar_senha"]:
                self._show_error("Confirme a nova senha.")
                return
            if data["senha"] != data["confirmar_senha"]:
                self._show_error("A confirmação da senha não confere.")
                return
            senha_hash = bcrypt.hashpw(
                data["senha"].encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

        conn = get_connection()
        if not conn:
            self._show_error("Falha ao conectar ao banco de dados.")
            return

        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM usuarios WHERE login = %s AND id <> %s",
                (data["login"], user_id)
            )
            exists = self._fetch_scalar(cursor)
            if exists:
                self._show_error("Já existe outro usuário com este login.")
                return

            if senha_hash:
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET login = %s,
                        nome = %s,
                        senha = %s,
                        is_admin = %s,
                        primeiro_login = %s
                    WHERE id = %s
                    """,
                    (
                        data["login"],
                        data["nome"],
                        senha_hash,
                        bool(data["is_admin"]),
                        bool(data["primeiro_login"]),
                        user_id,
                    )
                )
            else:
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET login = %s,
                        nome = %s,
                        is_admin = %s,
                        primeiro_login = %s
                    WHERE id = %s
                    """,
                    (
                        data["login"],
                        data["nome"],
                        bool(data["is_admin"]),
                        bool(data["primeiro_login"]),
                        user_id,
                    )
                )

            conn.commit()
            self.load_users()
            self._show_success("Usuário atualizado com sucesso.")
        except Exception as e:
            conn.rollback()
            logger.exception("Erro ao editar usuário")
            self._show_error(f"Erro ao editar usuário: {e}")
        finally:
            cursor.close()
            conn.close()

    def delete_user(self):
        row = self.table.currentRow()
        if row < 0:
            self._show_error("Selecione um usuário para excluir.")
            return

        user_id = self._get_selected_user_id()
        if user_id is None:
            self._show_error("Usuário inválido.")
            return

        nome = self.table.item(row, 2).text() if self.table.item(row, 2) else ""

        resposta = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Deseja realmente excluir o usuário '{nome}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if resposta != QMessageBox.StandardButton.Yes:
            return

        conn = get_connection()
        if not conn:
            self._show_error("Falha ao conectar ao banco de dados.")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
            conn.commit()
            self.load_users()
            self._show_success("Usuário excluído com sucesso.")
        except Exception as e:
            conn.rollback()
            logger.exception("Erro ao excluir usuário")
            self._show_error(f"Erro ao excluir usuário: {e}")
        finally:
            cursor.close()
            conn.close()

    def export_csv(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar usuários", "usuarios.csv", "CSV (*.csv)"
        )
        if not filename:
            return

        try:
            with open(filename, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "Login", "Nome", "É Admin?", "1º Login?"])

                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(5):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)

            self._show_success("Usuários exportados para CSV com sucesso.")
        except Exception as e:
            logger.exception("Erro ao exportar CSV")
            self._show_error(f"Erro ao exportar CSV: {e}")

    def export_pdf(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar usuários", "usuarios.pdf", "PDF (*.pdf)"
        )
        if not filename:
            return

        try:
            styles = getSampleStyleSheet()
            doc = SimpleDocTemplate(filename, pagesize=letter)

            data = [["ID", "Login", "Nome", "É Admin?", "1º Login?"]]
            for row in range(self.table.rowCount()):
                linha = []
                for col in range(5):
                    item = self.table.item(row, col)
                    texto = item.text() if item else ""
                    linha.append(Paragraph(texto, styles["BodyText"]))
                data.append(linha)

            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ]))

            doc.build([table])
            self._show_success("Usuários exportados para PDF com sucesso.")
        except Exception as e:
            logger.exception("Erro ao exportar PDF")
            self._show_error(f"Erro ao exportar PDF: {e}")