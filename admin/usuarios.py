# admin/usuarios.py

from PyQt5.QtWidgets import (
    QPushButton, QHBoxLayout, QVBoxLayout, QTableWidget, QMessageBox, QWidget,
    QHeaderView, QFileDialog, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
import csv

from autenticacao.session import is_admin
from autenticacao.autenticacao import hash_password
from database_module import get_connection  # psycopg3 via get_db_config()


class UsuarioDialog(QDialog):
    def __init__(self, login="", nome="", is_admin=0, primeiro_login="Sim", senha=""):
        super().__init__()
        self.setWindowTitle("Dados do Usuário")
        self.layout = QFormLayout(self)

        self.login_edit = QLineEdit(login)
        self.nome_edit = QLineEdit(nome)

        admin_text = "Sim" if is_admin in (1, "1", True, "t") else "Não"
        self.admin_edit = QLineEdit(admin_text)

        self.primeiro_edit = QLineEdit(primeiro_login)

        self.senha_edit = QLineEdit()
        self.senha_edit.setEchoMode(QLineEdit.Password)
        if senha:
            self.senha_edit.setText(senha)

        self.layout.addRow("Login:", self.login_edit)
        self.layout.addRow("Nome:", self.nome_edit)
        self.layout.addRow("Admin (Sim/Não):", self.admin_edit)
        self.layout.addRow("Primeiro Login (Sim/Não):", self.primeiro_edit)
        self.layout.addRow("Senha:", self.senha_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

    def get_data(self):
        texto_admin = self.admin_edit.text()
        is_admin_value = 1 if texto_admin.strip().lower() == "sim" else 0
        return {
            "login": self.login_edit.text().strip(),
            "nome": self.nome_edit.text().strip(),
            "is_admin": is_admin_value,
            "primeiro_login": self.primeiro_edit.text().strip(),
            "senha": self.senha_edit.text(),
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
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setColumnHidden(0, True)

        self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Adicionar")
        self.btn_edit = QPushButton("Editar")
        self.btn_del = QPushButton("Deletar")
        self.btn_marcar_primeiro = QPushButton("Marcar como 1º login")
        self.btn_exportar = QPushButton("Exportar CSV")

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_del)
        btn_layout.addWidget(self.btn_marcar_primeiro)
        btn_layout.addWidget(self.btn_exportar)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.btn_add.clicked.connect(self.add_user)
        self.btn_edit.clicked.connect(self.edit_user)
        self.btn_del.clicked.connect(self.delete_user)
        self.btn_marcar_primeiro.clicked.connect(self.marcar_primeiro_login)
        self.btn_exportar.clicked.connect(self.exportar_csv)

        print("DEBUG: UsuariosTab nova carregada")
        self.load_users()

    def _get_dash_main(self):
        janela = self.parentWidget()
        while janela is not None and janela.__class__.__name__ != "DashMain":
            janela = janela.parentWidget()
        return janela

    def _show_success(self, mensagem):
        dash = self._get_dash_main()
        if dash:
            dash.show_operation_done(mensagem)
        else:
            QMessageBox.information(self, "Sucesso", mensagem)

    def load_users(self):
        self.table.setRowCount(0)
        conn = get_connection()
        if conn is None:
            print("DEBUG: conn é None em load_users")
            return

        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, login, nome, is_admin, primeiro_login FROM usuarios ORDER BY login"
        )
        users = cursor.fetchall()
        print("DEBUG: users em UsuariosTab:", users)
        conn.close()

        self.table.setRowCount(len(users))
        for row_idx, user in enumerate(users):
            print("DEBUG preenchendo linha", row_idx, "->", user)
            user_id, login, nome, is_admin_flag, primeiro_login_flag = user

            if isinstance(login, (bytes, bytearray)):
                login = login.decode("utf-8")
            if isinstance(nome, (bytes, bytearray)):
                nome = nome.decode("utf-8")

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(user_id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(login)))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(nome)))

            texto_admin = "Sim" if is_admin_flag in (1, "1", True, "t") else "Não"
            item_admin = QTableWidgetItem(texto_admin)
            item_admin.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 3, item_admin)

            # coluna Primeiro Login com texto + cor
            is_primeiro = primeiro_login_flag in (1, "1", True, "t")
            texto_primeiro = "Sim" if is_primeiro else "Não"
            item_primeiro = QTableWidgetItem(texto_primeiro)
            item_primeiro.setTextAlignment(Qt.AlignCenter)
            if is_primeiro:
                item_primeiro.setForeground(QColor("red"))
            else:
                item_primeiro.setForeground(QColor("darkgreen"))
            self.table.setItem(row_idx, 4, item_primeiro)

    def _get_selected_user_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    def add_user(self):
        dlg = UsuarioDialog()
        if dlg.exec_() != QDialog.Accepted:
            return

        data = dlg.get_data()
        if not data["login"] or not data["nome"]:
            QMessageBox.warning(self, "Dados inválidos", "Login e Nome são obrigatórios.")
            return

        senha_clara = data["senha"].strip()
        if not senha_clara:
            QMessageBox.warning(self, "Dados inválidos", "Informe uma senha.")
            return

        senha_hash = hash_password(senha_clara)

        is_admin_bool = True if data["is_admin"] == 1 else False
        primeiro_flag = True if data["primeiro_login"].strip().lower() == "sim" else False

        conn = get_connection()
        if conn is None:
            QMessageBox.critical(self, "Erro", "Não foi possível conectar ao banco.")
            return

        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO usuarios (login, nome, senha, is_admin, primeiro_login)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (data["login"], data["nome"], senha_hash, is_admin_bool, primeiro_flag),
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao inserir usuário:\n{e}")
        finally:
            conn.close()

        self.load_users()
        self._show_success("Usuário cadastrado com sucesso!")

    def edit_user(self):
        user_id = self._get_selected_user_id()
        if user_id is None:
            QMessageBox.warning(self, "Seleção", "Selecione um usuário para editar.")
            return

        row = self.table.currentRow()
        login_item = self.table.item(row, 1)
        nome_item = self.table.item(row, 2)
        admin_item = self.table.item(row, 3)
        primeiro_item = self.table.item(row, 4)

        login = login_item.text() if login_item else ""
        nome = nome_item.text() if nome_item else ""
        admin_texto = admin_item.text() if admin_item else "Não"
        primeiro_texto = primeiro_item.text() if primeiro_item else "Não"

        is_admin_flag = 1 if admin_texto.strip().lower() == "sim" else 0

        dlg = UsuarioDialog(
            login=login,
            nome=nome,
            is_admin=is_admin_flag,
            primeiro_login=primeiro_texto,
            senha="",  # senha em branco; só altera se preencher
        )
        if dlg.exec_() != QDialog.Accepted:
            return

        data = dlg.get_data()

        is_admin_bool = True if data["is_admin"] == 1 else False
        primeiro_flag = True if data["primeiro_login"].strip().lower() == "sim" else False

        conn = get_connection()
        if conn is None:
            QMessageBox.critical(self, "Erro", "Não foi possível conectar ao banco.")
            return

        try:
            cur = conn.cursor()
            if data["senha"].strip():
                senha_hash = hash_password(data["senha"].strip())
                cur.execute(
                    """
                    UPDATE usuarios
                    SET login = %s, nome = %s, senha = %s, is_admin = %s, primeiro_login = %s
                    WHERE id = %s
                    """,
                    (
                        data["login"],
                        data["nome"],
                        senha_hash,
                        is_admin_bool,
                        primeiro_flag,
                        user_id,
                    ),
                )
            else:
                cur.execute(
                    """
                    UPDATE usuarios
                    SET login = %s, nome = %s, is_admin = %s, primeiro_login = %s
                    WHERE id = %s
                    """,
                    (
                        data["login"],
                        data["nome"],
                        is_admin_bool,
                        primeiro_flag,
                        user_id,
                    ),
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar usuário:\n{e}")
        finally:
            conn.close()

        self.load_users()
        self._show_success("Usuário atualizado com sucesso!")

    def delete_user(self):
        user_id = self._get_selected_user_id()
        if user_id is None:
            QMessageBox.warning(self, "Seleção", "Selecione um usuário para deletar.")
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar",
            "Tem certeza que deseja deletar este usuário?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resposta != QMessageBox.Yes:
            return

        conn = get_connection()
        if conn is None:
            QMessageBox.critical(self, "Erro", "Não foi possível conectar ao banco.")
            return

        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao deletar usuário:\n{e}")
        finally:
            conn.close()

        self.load_users()
        self._show_success("Usuário excluído com sucesso!")

    def marcar_primeiro_login(self):
        user_id = self._get_selected_user_id()
        if user_id is None:
            QMessageBox.warning(self, "Seleção", "Selecione um usuário para marcar como 1º login.")
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar",
            "Marcar este usuário como primeiro login?\n"
            "Ele será obrigado a trocar a senha no próximo acesso.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resposta != QMessageBox.Yes:
            return

        conn = get_connection()
        if conn is None:
            QMessageBox.critical(self, "Erro", "Não foi possível conectar ao banco.")
            return

        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE usuarios
                SET primeiro_login = TRUE
                WHERE id = %s
                """,
                (user_id,),
            )
            conn.commit()
            self._show_success("Usuário marcado como primeiro login.")

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar usuário:\n{e}")
        finally:
            conn.close()

        self.load_users()

    def exportar_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar CSV", "", "Arquivos CSV (*.csv);;Todos os arquivos (*.*)"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile, delimiter=";")
                headers = ["ID", "Login", "Nome", "Admin", "Primeiro Login"]
                writer.writerow(headers)

                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)

            self._show_success("CSV de usuários exportado com sucesso!")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV:\n{e}")
