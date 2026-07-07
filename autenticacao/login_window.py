# autenticacao/login_window.py

import traceback

from PyQt6.QtWidgets import (
    QDialog,
    QMessageBox,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QDialogButtonBox,
)

from autenticacao.session import session_manager
from autenticacao.autenticacao import (
    get_user_by_login,
    verify_password,
    hash_password,
)
from database_module import execute_query
from utils.utils_log import log_acao


class PasswordChangeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alterar senha (primeiro acesso)")
        self.resize(320, 180)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.nova_senha = QLineEdit()
        self.nova_senha.setEchoMode(QLineEdit.EchoMode.Password)

        self.confirma_senha = QLineEdit()
        self.confirma_senha.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("Nova senha:", self.nova_senha)
        form.addRow("Confirmar senha:", self.confirma_senha)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def get_data(self):
        return self.nova_senha.text().strip(), self.confirma_senha.text().strip()


class LoginWindow(QDialog):
    def __init__(self, on_login_success=None, parent=None):
        super().__init__(parent)
        self.on_login_success = on_login_success

        self.setWindowTitle("Login Sistema Controle de Chaves")
        self.resize(320, 160)
        self.setModal(True)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.line_login = QLineEdit()
        self.line_senha = QLineEdit()
        self.line_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.line_senha.returnPressed.connect(self.try_login)

        form.addRow("Login:", self.line_login)
        form.addRow("Senha:", self.line_senha)

        self.btn_login = QPushButton("Entrar")
        self.btn_login.clicked.connect(self.try_login)

        layout.addLayout(form)
        layout.addWidget(self.btn_login)

        self.line_login.setFocus()

    def try_login(self):
        login = self.line_login.text().strip()
        senha = self.line_senha.text().strip()

        if not login or not senha:
            QMessageBox.warning(self, "Erro", "Informe login e senha.")
            return

        try:
            user = get_user_by_login(login)

            if user is None:
                log_acao(
                    action="Tentativa de login",
                    user=login,
                    resource="autenticacao",
                    status="failed",
                    details="utilizador_nao_encontrado",
                )
                QMessageBox.warning(self, "Erro", "Utilizador não encontrado.")
                return

            login_db = user.get("login")
            senha_hash = user.get("senha")
            primeiro_login = user.get("primeiro_login", False)
            ativo = user.get("ativo", True)

            if isinstance(login_db, bytes):
                login_db = login_db.decode("utf-8", errors="ignore")

            if isinstance(senha_hash, str):
                senha_hash = senha_hash.encode("utf-8")

            if isinstance(primeiro_login, str):
                primeiro_login = primeiro_login.strip().lower() in (
                    "1", "true", "t", "sim", "yes"
                )
            else:
                primeiro_login = bool(primeiro_login)

            if isinstance(ativo, str):
                ativo = ativo.strip().lower() in (
                    "1", "true", "t", "sim", "yes"
                )
            else:
                ativo = bool(ativo)

            if not ativo:
                log_acao(
                    action="Tentativa de login",
                    user=login_db or login,
                    resource="autenticacao",
                    status="failed",
                    details=f'utilizador_inativo; utilizador_id={user["id"]}',
                )
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Usuário inativo. Contate o administrador."
                )
                return

            if not verify_password(senha_hash, senha):
                log_acao(
                    action="Tentativa de login",
                    user=login_db or login,
                    resource="autenticacao",
                    status="failed",
                    details=f'senha_invalida; utilizador_id={user["id"]}',
                )
                QMessageBox.warning(self, "Erro", "Senha inválida.")
                self.line_senha.clear()
                self.line_senha.setFocus()
                return

            if primeiro_login:
                dlg = PasswordChangeDialog(self)
                if dlg.exec() != QDialog.DialogCode.Accepted:
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

                if len(nova_senha) < 6:
                    QMessageBox.warning(
                        self,
                        "Erro",
                        "A nova senha deve ter pelo menos 6 caracteres.",
                    )
                    return

                if nova_senha != confirma:
                    QMessageBox.warning(self, "Erro", "As senhas não coincidem.")
                    return

                novo_hash = hash_password(nova_senha)

                execute_query(
                    """
                    UPDATE usuarios
                    SET senha = %s, primeiro_login = FALSE
                    WHERE id = %s
                    """,
                    (novo_hash, user["id"]),
                    fetchone=False,
                )

                user["senha"] = novo_hash
                user["primeiro_login"] = False

                log_acao(
                    action="Alteração de senha no primeiro acesso",
                    user=login_db,
                    resource="autenticacao",
                    status="success",
                    details=f'utilizador_id={user["id"]}',
                )

            try:
                sessao_ok = session_manager.login(login_db)
                print("LOGIN RECEBIDO:", repr(login_db))
                print("RESULTADO session_manager.login():", sessao_ok)
            except Exception as e:
                traceback.print_exc()

                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Falha ao carregar sessão do usuário.\n\n{type(e).__name__}: {e}\n\nVeja o terminal para o traceback completo."
                )
                raise

            if not sessao_ok:
                log_acao(
                    action="Tentativa de login",
                    user=login_db or login,
                    resource="autenticacao",
                    status="failed",
                    details=f'falha_ao_carregar_sessao; utilizador_id={user["id"]}',
                )
                QMessageBox.warning(
                    self,
                    "Erro",
                    f"Falha ao carregar sessão do usuário.\n\nLogin usado na sessão: {login_db!r}"
                )
                return

            log_acao(
                action="Login realizado",
                user=login_db,
                resource="autenticacao",
                status="success",
                details=f'utilizador_id={user["id"]}',
            )

            QMessageBox.information(self, "Sucesso", "Login realizado com sucesso.")

            user_atual = session_manager.current_user
            if self.on_login_success:
                self.on_login_success(user_atual)

            self.accept()

        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Erro",
                f"Ocorreu um erro interno ao tentar efetuar o login.\n\n{type(e).__name__}: {e}\n\nVeja o terminal para o traceback completo."
            )
            raise