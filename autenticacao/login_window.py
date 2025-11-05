from PyQt5.QtWidgets import QWidget, QLineEdit, QLabel, QPushButton, QVBoxLayout, QMessageBox, QDialog, QFormLayout, QDialogButtonBox
from . import get_user_by_login, verify_password, hash_password, show_info, show_warning
from database_module import execute_query
from .session import session_manager

class ChangePasswordDialog(QDialog):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Trocar Senha - Primeiro Login")
        self.layout = QFormLayout(self)
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.layout.addRow("Nova Senha:", self.new_password)
        self.layout.addRow("Confirme Senha:", self.confirm_password)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.change_password)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def change_password(self):
        pw = self.new_password.text()
        confirm = self.confirm_password.text()
        if not pw or not confirm:
            show_warning("Erro", "Preencha ambos os campos de senha.")
            return
        if pw != confirm:
            show_warning("Erro", "As senhas não conferem.")
            return
        senha_hashed = hash_password(pw)
        query = "UPDATE usuarios SET senha = ?, primeiro_login = 0 WHERE id = ?"
        execute_query(query, (senha_hashed, self.user_id))
        show_info("Sucesso", "Senha alterada com sucesso!")
        self.accept()

class LoginWindow(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.setWindowTitle("Login Sistema Controle de Chaves")
        self.setGeometry(100, 100, 300, 150)
        layout = QVBoxLayout()
        self.label_login = QLabel("Login:")
        self.input_login = QLineEdit()
        layout.addWidget(self.label_login)
        layout.addWidget(self.input_login)
        self.label_senha = QLabel("Senha:")
        self.input_senha = QLineEdit()
        self.input_senha.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.label_senha)
        layout.addWidget(self.input_senha)
        self.btn_entrar = QPushButton("Entrar")
        self.btn_entrar.clicked.connect(self.try_login)
        layout.addWidget(self.btn_entrar)
        self.setLayout(layout)

    def try_login(self):
        login = self.input_login.text().strip()
        senha = self.input_senha.text().strip()

        #print(f"Tentativa de login com login: {login} e senha: {senha}")

        if not login or not senha:
            QMessageBox.warning(self, "Erro", "Preencha login e senha.")
            return

        user = get_user_by_login(login)
        #print(f"Usuário recuperado do banco: {user}")

        if user:
            user = dict(user)  # <-- CORREÇÃO FUNDAMENTAL: converte para dict, compatível com .get() e [ ]
            senha_banco = user['senha']
            print(f"Hash armazenado: {senha_banco}")

            hash_valido = senha_banco and senha_banco.startswith("$2b$")
            if not hash_valido:
                show_warning("Atenção", "Sua senha está salva de forma insegura. Você precisa trocá-la para continuar.")
                dialog = ChangePasswordDialog(user["id"])
                if dialog.exec_() == QDialog.Accepted:
                    QMessageBox.information(self, "Sucesso", "Senha cadastrada com segurança! Faça login novamente.")
                    self.input_login.clear()
                    self.input_senha.clear()
                    return
                else:
                    QMessageBox.warning(self, "Aviso", "Troca de senha obrigatória cancelada.")
                    return

            senha_valida = verify_password(senha_banco, senha)
            print(f"Senha válida? {senha_valida}")

            if senha_valida:
                try:
                    if user["primeiro_login"]:
                        dialog = ChangePasswordDialog(user["id"])
                        resultado = dialog.exec_()
                        if resultado == QDialog.Accepted:
                            session_manager.login(user["login"], user["is_admin"])
                            self.on_login_success(user)
                            self.close()
                        else:
                            show_warning("Aviso", "É necessário trocar a senha para continuar.")
                            self.input_senha.clear()
                            self.input_login.setFocus()
                    else:
                        session_manager.login(user["login"], user["is_admin"])
                        QMessageBox.information(self, "Sucesso", "Login realizado com sucesso.")
                        self.on_login_success(user)
                        self.close()
                except Exception as e:
                    print(f"Erro na transição de telas: {e}")
                    show_warning("Erro", f"Erro na transição de telas: {e}")
            else:
                QMessageBox.warning(self, "Erro", "Login ou senha incorretos.")
        else:
            QMessageBox.warning(self, "Erro", "Login ou senha incorretos.")
