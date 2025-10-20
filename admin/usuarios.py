from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QMessageBox,
    QHBoxLayout, QDialog, QFormLayout, QDialogButtonBox, QLineEdit, QCheckBox, QTableWidgetItem
)
from database_module import execute_query
from autenticacao.session import is_admin

class UserDialog(QDialog):
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastro de Usuário" if user_data is None else "Editar Usuário")
        self.user_data = user_data
        self.layout = QFormLayout(self)
        self.login_field = QLineEdit()
        self.nome_field = QLineEdit()
        self.senha_field = QLineEdit()
        self.senha_field.setEchoMode(QLineEdit.Password)
        self.admin_checkbox = QCheckBox("Administrador")
        self.layout.addRow("Login:", self.login_field)
        self.layout.addRow("Nome:", self.nome_field)
        self.layout.addRow("Senha:", self.senha_field)
        self.layout.addRow(self.admin_checkbox)
        if self.user_data:
            self.login_field.setText(self.user_data["login"])
            self.login_field.setReadOnly(True)
            self.nome_field.setText(self.user_data["nome"])
            self.admin_checkbox.setChecked(bool(self.user_data["is_admin"]))
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_data(self):
        return {
            "login": self.login_field.text().strip(),
            "nome": self.nome_field.text().strip(),
            "senha": self.senha_field.text(),
            "is_admin": 1 if self.admin_checkbox.isChecked() else 0
        }

class UsuariosTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestão de Usuários")
        self.resize(600, 400)
        if not is_admin():
            QMessageBox.warning(self, "Acesso Negado", "Você não tem permissão de administrador.")
            self.close()
            return
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Login", "Nome", "Admin", "Primeiro Login"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Adicionar")
        self.btn_edit = QPushButton("Editar")
        self.btn_del = QPushButton("Deletar")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_del)
        layout.addLayout(btn_layout)
        self.btn_add.clicked.connect(self.add_user)
        self.btn_edit.clicked.connect(self.edit_user)
        self.btn_del.clicked.connect(self.delete_user)
        self.load_users()

    def load_users(self):
        self.table.setRowCount(0)
        users = execute_query("SELECT id, login, nome, is_admin, primeiro_login FROM usuarios", (), fetchall=True)
        for idx, user in enumerate(users):
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(str(user["id"])))
            self.table.setItem(idx, 1, QTableWidgetItem(user["login"]))
            self.table.setItem(idx, 2, QTableWidgetItem(user["nome"]))
            self.table.setItem(idx, 3, QTableWidgetItem("Sim" if user["is_admin"] else "Não"))
            self.table.setItem(idx, 4, QTableWidgetItem("Sim" if user["primeiro_login"] else "Não"))

    def add_user(self):
        dialog = UserDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                execute_query(
                    "INSERT INTO usuarios (login, nome, senha, is_admin, primeiro_login) VALUES (?, ?, ?, ?, 1)",
                    (data["login"], data["nome"], data["senha"], data["is_admin"])
                )
                QMessageBox.information(self, "Sucesso", "Usuário cadastrado com sucesso.")
                self.load_users()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cadastrar usuário: {e}")

    def edit_user(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Selecione", "Selecione um usuário para editar.")
            return
        login = self.table.item(selected, 1).text()
        user_data = execute_query("SELECT * FROM usuarios WHERE login = ?", (login,), fetchone=True)
        dialog = UserDialog(self, user_data)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                if data["senha"]:
                    execute_query(
                        "UPDATE usuarios SET nome=?, senha=?, is_admin=? WHERE login=?",
                        (data["nome"], data["senha"], data["is_admin"], login)
                    )
                else:
                    execute_query(
                        "UPDATE usuarios SET nome=?, is_admin=? WHERE login=?",
                        (data["nome"], data["is_admin"], login)
                    )
                QMessageBox.information(self, "Sucesso", "Usuário alterado com sucesso.")
                self.load_users()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao editar usuário: {e}")

    def delete_user(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Selecione", "Selecione um usuário para excluir.")
            return
        login = self.table.item(selected, 1).text()
        resp = QMessageBox.question(self, "Confirmação", f"Deseja excluir o usuário '{login}'?")
        if resp == QMessageBox.Yes:
            try:
                execute_query("DELETE FROM usuarios WHERE login=?", (login,))
                QMessageBox.information(self, "Sucesso", "Usuário excluído.")
                self.load_users()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir usuário: {e}")
