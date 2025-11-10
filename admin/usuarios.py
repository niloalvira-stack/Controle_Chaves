import sqlite3
from PyQt5.QtWidgets import (
    QPushButton, QHBoxLayout, QVBoxLayout, QTableWidget, QMessageBox, QWidget, QHeaderView, QFileDialog,
    QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox
)
from autenticacao import is_admin, hash_password  # hash_password deve estar implementada


def get_db_connection():
    return sqlite3.connect("controle_chaves.db")


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
            "login": self.login_edit.text(),
            "nome": self.nome_edit.text(),
            "is_admin": is_admin_value,
            "primeiro_login": self.primeiro_edit.text(),
            "senha": self.senha_edit.text()
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
        self.table.setColumnHidden(0, True)

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
        self.load_users()

    def load_users(self):
        self.table.setRowCount(0)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, login, nome, is_admin, primeiro_login FROM usuarios")
        users = cursor.fetchall()
        conn.close()

        for row_idx, user in enumerate(users):
            self.table.insertRow(row_idx)
            for col_idx, value in enumerate(user):
                if col_idx == 3:  # is_admin
                    texto_admin = "Sim" if value in (1, "1", True) else "Não"
                    item = QTableWidgetItem(texto_admin)
                else:
                    item = QTableWidgetItem(str(value if value else ""))
                self.table.setItem(row_idx, col_idx, item)

    def add_user(self):
        dialog = UsuarioDialog()
        if dialog.exec():
            dados = dialog.get_data()
            # Validação simples
            if not dados["login"] or not dados["senha"]:
                QMessageBox.warning(self, "Erro", "Login e senha são obrigatórios.")
                return
            hashed_pw = hash_password(dados["senha"])
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usuarios (login, nome, is_admin, primeiro_login, senha) VALUES (?, ?, ?, ?, ?)",
                (dados["login"], dados["nome"], dados["is_admin"], dados["primeiro_login"], hashed_pw)
            )
            conn.commit()
            conn.close()
            self.load_users()
            QMessageBox.information(self, "Adicionar Usuário", "Usuário cadastrado com sucesso!")

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

        # Buscar senha atual do banco — CORREÇÃO: fetchone() só uma vez!
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT senha FROM usuarios WHERE id=?", (user_id,))
        senha_row = cursor.fetchone()
        senha_atual = senha_row[0] if senha_row else ""
        conn.close()

        # Cria diálogo (senha inicial em branco)
        dialog = UsuarioDialog(login, nome, is_admin_value, primeiro_login, "")
        if dialog.exec():
            dados = dialog.get_data()
            nova_senha = dados["senha"]
            # Só troca senha se o admin digitar algo!
            if nova_senha:
                from autenticacao import hash_password
                hashed_pw = hash_password(nova_senha)
            else:
                hashed_pw = senha_atual
            # Atualiza tudo, incluindo senha (hash ou mantida)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET login=?, nome=?, is_admin=?, primeiro_login=?, senha=? WHERE id=?",
                (dados["login"], dados["nome"], dados["is_admin"], dados["primeiro_login"], hashed_pw, user_id)
            )
            conn.commit()
            conn.close()
            self.load_users()
            QMessageBox.information(self, "Editar Usuário", "Usuário editado com sucesso!")

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
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id=?", (user_id,))
            conn.commit()
            conn.close()
            self.load_users()
            QMessageBox.information(self, "Excluído", f"Usuário '{nome}' excluído!")

    def exportar_csv(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "Arquivo CSV (*.csv)")
        if caminho:
            try:
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write("Login;Nome;Admin;Primeiro Login\n")
                    for row in range(self.table.rowCount()):
                        login = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
                        nome = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
                        admin = self.table.item(row, 3).text() if self.table.item(row, 3) else ""
                        primeiro = self.table.item(row, 4).text() if self.table.item(row, 4) else ""
                        f.write(f"{login};{nome};{admin};{primeiro}\n")
                QMessageBox.information(self, "Exportação", "Exportação concluída!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV: {e}")
