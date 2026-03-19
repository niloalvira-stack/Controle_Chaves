# autenticacao/login_window.py

import traceback

from PyQt5.QtWidgets import (
    QWidget,
    QMessageBox,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QDialog,
    QDialogButtonBox,
)

from autenticacao.session import session_manager
from autenticacao.autenticacao import (
    get_user_by_login,
    verify_password,
    hash_password,
    execute_query,
)


class PasswordChangeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alterar senha (primeiro acesso)")
        self.resize(320, 180)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.nova_senha = QLineEdit()
        self.nova_senha.setEchoMode(QLineEdit.Password)
        self.confirma_senha = QLineEdit()
        self.confirma_senha.setEchoMode(QLineEdit.Password)

        form.addRow("Nova senha:", self.nova_senha)
        form.addRow("Confirmar senha:", self.confirma_senha)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def get_data(self):
        return self.nova_senha.text().strip(), self.confirma_senha.text().strip()


class LoginWindow(QWidget):
    def __init__(self, on_login_success=None, parent=None):
        super().__init__(parent)
        self.on_login_success = on_login_success

        self.setWindowTitle("Login Sistema Controle de Chaves")
        self.resize(320, 160)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.line_login = QLineEdit()
        self.line_senha = QLineEdit()

        self.line_senha.setEchoMode(QLineEdit.Password)

        form.addRow("Login:", self.line_login)
        form.addRow("Senha:", self.line_senha)

        self.btn_login = QPushButton("Entrar")
        self.btn_login.clicked.connect(self.try_login)

        layout.addLayout(form)
        layout.addWidget(self.btn_login)

    def try_login(self):
        login = self.line_login.text().strip()
        senha = self.line_senha.text().strip()
        ...

        try:
            user = get_user_by_login(login)

            if user is None:
                QMessageBox.warning(self, "Erro", "Utilizador não encontrado.")
                return

            # aqui segue validação de senha, etc.

            print(
                "DEBUG user dict no login:",
                user,
                type(user.get("primeiro_login")),
                user.get("primeiro_login"),
            )

            if not verify_password(user["senha"], senha):
                QMessageBox.warning(self, "Erro", "Senha inválida.")
                return

            print("Senha válida? True")

            # Primeiro login: força troca de senha
            if user.get("primeiro_login") is True:
                dlg = PasswordChangeDialog(self)
                if dlg.exec_() != QDialog.Accepted:
                    QMessageBox.information(
                        self,
                        "Aviso",
                        "É necessário alterar a senha no primeiro acesso.",
                    )
                    return

                nova_senha, confirma = dlg.get_data()
                if not nova_senha:
                    QMessageBox.warning(self, "Erro", "Nova senha não pode ser vazia.")
                    return
                if nova_senha != confirma:
                    QMessageBox.warning(self, "Erro", "As senhas não coincidem.")
                    return

                novo_hash = hash_password(nova_senha)

                print("DEBUG: atualizando senha e primeiro_login para usuário", user["id"])
                try:
                    execute_query(
                        """
                        UPDATE usuarios
                        SET senha = %s, primeiro_login = FALSE
                        WHERE id = %s
                        """,
                        (novo_hash, user["id"]),
                        fetchone=False,
                    )
                    print("DEBUG: UPDATE primeiro_login executado")
                except Exception as e:
                    print("DEBUG ERRO no UPDATE primeiro_login:", e)
                    QMessageBox.critical(
                        self,
                        "Erro",
                        f"Erro ao atualizar senha no primeiro login:\n{e}",
                    )
                    return

                user["senha"] = novo_hash
                user["primeiro_login"] = False

            print("DEBUG: antes de session_manager.login")
            login_str = str(user["login"])
            print("DEBUG: login_str type =", type(login_str), repr(login_str))

            if not session_manager.login(login_str):
                print("DEBUG: session_manager.login retornou False")
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Falha ao carregar sessão do usuário."
                )
                return

            QMessageBox.information(self, "Sucesso", "Login realizado com sucesso.")

            print("DEBUG: antes de on_login_success")
            user_atual = session_manager.current_user
            print("DEBUG user_atual após login:", user_atual)

            if self.on_login_success:
                self.on_login_success(user_atual)

            print("DEBUG: depois de on_login_success (antes de close)")
            self.close()

        except Exception:
            erro = traceback.format_exc()
            print("ERRO interno no try_login:", erro)
            QMessageBox.critical(
                self,
                "Erro",
                "Ocorreu um erro interno ao tentar efetuar o login.",
            )
