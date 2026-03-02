from PyQt5.QtWidgets import (
    QPushButton, QHBoxLayout, QVBoxLayout, QTableWidget, QMessageBox, QWidget,
    QHeaderView, QFileDialog, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox
)
import csv

from autenticacao import is_admin, hash_password
from database_module import get_connection  # usa o mesmo banco (AppData)


class UsuarioDialog(QDialog):
    def __init__(self, login="", nome="", is_admin=0, primeiro_login="Sim", senha=""):
        super().__init__()
        self.setWindowTitle("Dados do Usuário")
        self.layout = QFormLayout(self)

        self.login_edit = QLineEdit(login)
        self.nome_edit = QLineEdit(nome)

        admin_text = "Sim" if is_admin in (1, "1", True) else "Não"
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

        # Ajustes visuais extra
        self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Adicionar")
        self.btn_edit = QPushButton("Editar")
        self.btn_del = QPushButton("Deletar")
        self.btn_exportar = QPushButton("Exportar CSV")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_del)
        btn_layout.addWidget(self.btn_exportar)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.btn_add.clicked.connect(self.add_user)
        self.btn_edit.clicked.connect(self.edit_user)
        self.btn_del.clicked.connect(self.delete_user)
        self.btn_exportar.clicked.connect(self.exportar_csv)

        print("DEBUG: UsuariosTab nova carregada")
        self.load_users()

    def _get_dash_main(self):
        janela = self.parentWidget()
        while janela is not None and janela.__class__.__name__ != "DashMain":
            janela = janela.parentWidget()
        return janela

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
            # user é RealDictRow (dict)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(user["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(user["login"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(user["nome"]))

            texto_admin = "Sim" if user["is_admin"] in (1, "1", True, "t") else "Não"
            self.table.setItem(row_idx, 3, QTableWidgetItem(texto_admin))

            texto_primeiro = "Sim" if user["primeiro_login"] in (1, "1", True, "t") else "Não"
            self.table.setItem(row_idx, 4, QTableWidgetItem(texto_primeiro))



    def add_user(self):
        dialog = UsuarioDialog()
        if dialog.exec():
            dados = dialog.get_data()

            if not dados["login"] or not dados["senha"]:
                QMessageBox.warning(self, "Erro", "Login e senha são obrigatórios.")
                return

            try:
                hashed_pw = hash_password(dados["senha"])
                conn = get_connection()
                if conn is None:
                    return
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO usuarios (login, nome, is_admin, primeiro_login, senha_hash)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (dados["login"], dados["nome"], dados["is_admin"],
                     dados["primeiro_login"], hashed_pw),
                )
                conn.commit()
                conn.close()
                self.load_users()

                dash = self._get_dash_main()
                if dash is not None:
                    dash.show_operation_done("Usuário criado")
            except Exception as e:
                if "UNIQUE" in str(e).upper():
                    QMessageBox.warning(self, "Erro", "Já existe um usuário com este login.")
                else:
                    QMessageBox.critical(self, "Erro", f"Erro ao cadastrar usuário: {e}")

    def edit_user(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Atenção", "Selecione um usuário para editar!")
            return

        row = selected[0].row()
        user_id = self.table.item(row, 0).text()
        login = self.table.item(row, 1).text()
        nome = self.table.item(row, 2).text()
        texto_admin = self.table.item(row, 3).text()
        is_admin_value = 1 if texto_admin.strip().lower() == "sim" else 0
        primeiro_login = self.table.item(row, 4).text()

        conn = get_connection()
        if conn is None:
            return
        cursor = conn.cursor()
        cursor.execute("SELECT senha_hash FROM usuarios WHERE id=%s", (user_id,))
        senha_row = cursor.fetchone()
        # senha_row será RealDictRow ou tupla conforme cursor_factory; aqui só precisamos do valor
        if isinstance(senha_row, dict):
            senha_atual = list(senha_row.values())[0] if senha_row else None
        else:
            senha_atual = senha_row[0] if senha_row else None
        conn.close()

        dialog = UsuarioDialog(login, nome, is_admin_value, primeiro_login, "")
        if dialog.exec():
            dados = dialog.get_data()
            nova_senha = dados["senha"]

            if nova_senha:
                hashed_pw = hash_password(nova_senha)
            else:
                hashed_pw = senha_atual

            try:
                conn = get_connection()
                if conn is None:
                    return
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET login=%s, nome=%s, is_admin=%s, primeiro_login=%s, senha_hash=%s
                    WHERE id=%s
                    """,
                    (
                        dados["login"],
                        dados["nome"],
                        dados["is_admin"],
                        dados["primeiro_login"],
                        hashed_pw,
                        user_id,
                    ),
                )
                conn.commit()
                conn.close()
                self.load_users()

                dash = self._get_dash_main()
                if dash is not None:
                    dash.show_operation_done("Usuário editado")
            except Exception as e:
                if "UNIQUE" in str(e).upper():
                    QMessageBox.warning(self, "Erro", "Já existe um usuário com este login.")
                else:
                    QMessageBox.critical(self, "Erro", f"Erro ao editar usuário: {e}")

    def delete_user(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Atenção", "Selecione um usuário para deletar!")
            return

        row = selected[0].row()
        user_id = self.table.item(row, 0).text()
        nome = self.table.item(row, 2).text()

        reply = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Deseja realmente excluir o usuário '{nome}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            conn = get_connection()
            if conn is None:
                return
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id=%s", (user_id,))
            conn.commit()
            conn.close()
            self.load_users()

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Usuário excluído")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir usuário: {e}")

    def exportar_csv(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "Arquivo CSV (*.csv)")
        if not caminho:
            return

        try:
            with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["Login", "Nome", "Admin", "Primeiro Login"])
                for row in range(self.table.rowCount()):
                    login = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
                    nome = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
                    admin = self.table.item(row, 3).text() if self.table.item(row, 3) else ""
                    primeiro = self.table.item(row, 4).text() if self.table.item(row, 4) else ""
                    writer.writerow([login, nome, admin, primeiro])

            dash = self._get_dash_main()
            if dash is not None:
                dash.show_operation_done("Exportação de usuários concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV: {e}")
