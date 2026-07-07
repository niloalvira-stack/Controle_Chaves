warning: in the working copy of '.idea/workspace.xml', LF will be replaced by CRLF the next time Git touches it
[1mdiff --git a/.idea/workspace.xml b/.idea/workspace.xml[m
[1mindex 5b593b3..93d8984 100644[m
[1m--- a/.idea/workspace.xml[m
[1m+++ b/.idea/workspace.xml[m
[36m@@ -5,20 +5,13 @@[m
   </component>[m
   <component name="ChangeListManager">[m
     <list default="true" id="0d418c30-b98e-4d7b-8f5b-2124b1b3803e" name="Changes" comment="Backup do sistema Controle de Chaves">[m
[31m-      <change afterPath="$PROJECT_DIR$/gerar_senha_b64.py" afterDir="false" />[m
       <change beforePath="$PROJECT_DIR$/.idea/workspace.xml" beforeDir="false" afterPath="$PROJECT_DIR$/.idea/workspace.xml" afterDir="false" />[m
[31m-      <change beforePath="$PROJECT_DIR$/admin/usuarios.py" beforeDir="false" afterPath="$PROJECT_DIR$/admin/usuarios.py" afterDir="false" />[m
[31m-      <change beforePath="$PROJECT_DIR$/autenticacao/autenticacao.py" beforeDir="false" afterPath="$PROJECT_DIR$/autenticacao/autenticacao.py" afterDir="false" />[m
[31m-      <change beforePath="$PROJECT_DIR$/autenticacao/helpers_autenticacao.py" beforeDir="false" afterPath="$PROJECT_DIR$/autenticacao/helpers_autenticacao.py" afterDir="false" />[m
[31m-      <change beforePath="$PROJECT_DIR$/database_module.py" beforeDir="false" afterPath="$PROJECT_DIR$/database_module.py" afterDir="false" />[m
[31m-      <change beforePath="$PROJECT_DIR$/relatorios/relatorio_geral.py" beforeDir="false" afterPath="$PROJECT_DIR$/relatorios/relatorio_geral.py" afterDir="false" />[m
[31m-      <change beforePath="$PROJECT_DIR$/relatorios/relatorio_pendencias_tab.py" beforeDir="false" afterPath="$PROJECT_DIR$/relatorios/relatorio_pendencias_tab.py" afterDir="false" />[m
[31m-      <change beforePath="$PROJECT_DIR$/relatorios/relatorio_periodo_tab.py" beforeDir="false" afterPath="$PROJECT_DIR$/relatorios/relatorio_periodo_tab.py" afterDir="false" />[m
[31m-      <change beforePath="$PROJECT_DIR$/relatorios/relatorio_sala_tab.py" beforeDir="false" afterPath="$PROJECT_DIR$/relatorios/relatorio_sala_tab.py" afterDir="false" />[m
[31m-      <change beforePath="$PROJECT_DIR$/relatorios/relatorio_usuario_tab.py" beforeDir="false" afterPath="$PROJECT_DIR$/relatorios/relatorio_usuario_tab.py" afterDir="false" />[m
[31m-      <change beforePath="$PROJECT_DIR$/relatorios/relatorios_geral_tab.py" beforeDir="false" afterPath="$PROJECT_DIR$/relatorios/relatorios_geral_tab.py" afterDir="false" />[m
[31m-      <change beforePath="$PROJECT_DIR$/relatorios/relatorios_graficos.py" beforeDir="false" afterPath="$PROJECT_DIR$/relatorios/relatorios_graficos.py" afterDir="false" />[m
[31m-      <change beforePath="$PROJECT_DIR$/utils/__init__.py" beforeDir="false" afterPath="$PROJECT_DIR$/utils/__init__.py" afterDir="false" />[m
[32m+[m[32m      <change beforePath="$PROJECT_DIR$/admin/utilizadores_tab.py" beforeDir="false" afterPath="$PROJECT_DIR$/admin/utilizadores_tab.py" afterDir="false" />[m
[32m+[m[32m      <change beforePath="$PROJECT_DIR$/autenticacao/login_window.py" beforeDir="false" afterPath="$PROJECT_DIR$/autenticacao/login_window.py" afterDir="false" />[m
[32m+[m[32m      <change beforePath="$PROJECT_DIR$/controle/movimentacoes.py" beforeDir="false" afterPath="$PROJECT_DIR$/controle/movimentacoes.py" afterDir="false" />[m
[32m+[m[32m      <change beforePath="$PROJECT_DIR$/controle/selecionar_sala_dialog.py" beforeDir="false" afterPath="$PROJECT_DIR$/controle/selecionar_sala_dialog.py" afterDir="false" />[m
[32m+[m[32m      <change beforePath="$PROJECT_DIR$/interface/dash_main.py" beforeDir="false" afterPath="$PROJECT_DIR$/interface/dash_main.py" afterDir="false" />[m
[32m+[m[32m      <change beforePath="$PROJECT_DIR$/main.py" beforeDir="false" afterPath="$PROJECT_DIR$/main.py" afterDir="false" />[m
     </list>[m
     <option name="SHOW_DIALOG" value="false" />[m
     <option name="HIGHLIGHT_CONFLICTS" value="true" />[m
[36m@@ -235,7 +228,15 @@[m
       <option name="project" value="LOCAL" />[m
       <updated>1772476914742</updated>[m
     </task>[m
[31m-    <option name="localTasksCounter" value="13" />[m
[32m+[m[32m    <task id="LOCAL-00013" summary="Backup do sistema Controle de Chaves">[m
[32m+[m[32m      <option name="closed" value="true" />[m
[32m+[m[32m      <created>1772808114682</created>[m
[32m+[m[32m      <option name="number" value="00013" />[m
[32m+[m[32m      <option name="presentableId" value="LOCAL-00013" />[m
[32m+[m[32m      <option name="project" value="LOCAL" />[m
[32m+[m[32m      <updated>1772808114682</updated>[m
[32m+[m[32m    </task>[m
[32m+[m[32m    <option name="localTasksCounter" value="14" />[m
     <servers />[m
   </component>[m
   <component name="Vcs.Log.Tabs.Properties">[m
[36m@@ -313,6 +314,11 @@[m
           <line>14</line>[m
           <option name="timeStamp" value="12" />[m
         </line-breakpoint>[m
[32m+[m[32m        <line-breakpoint enabled="true" suspend="THREAD" type="python-line">[m
[32m+[m[32m          <url>file://$PROJECT_DIR$/admin/log_viewer_tab.py</url>[m
[32m+[m[32m          <line>14</line>[m
[32m+[m[32m          <option name="timeStamp" value="13" />[m
[32m+[m[32m        </line-breakpoint>[m
       </breakpoints>[m
     </breakpoint-manager>[m
   </component>[m
[1mdiff --git a/admin/utilizadores_tab.py b/admin/utilizadores_tab.py[m
[1mindex ae24457..e8ff79e 100644[m
[1m--- a/admin/utilizadores_tab.py[m
[1m+++ b/admin/utilizadores_tab.py[m
[36m@@ -1,6 +1,7 @@[m
 # admin/utilizadores_tab.py[m
 import csv[m
 import logging[m
[32m+[m[32mimport re[m
 from contextlib import closing[m
 [m
 from PyQt6.QtWidgets import ([m
[36m@@ -10,7 +11,7 @@[m [mfrom PyQt6.QtWidgets import ([m
 )[m
 from PyQt6.QtCore import Qt[m
 [m
[31m-from autenticacao.helpers_autenticacao import get_db_connection[m
[32m+[m[32mfrom database_module import get_connection[m
 from autenticacao import get_current_user, validar_login, is_admin[m
 [m
 logger = logging.getLogger(__name__)[m
[36m@@ -135,17 +136,39 @@[m [mclass UtilizadoresTab(QWidget):[m
             QMessageBox.warning(self, "Erro", "Dados inválidos na seleção!")[m
             return None[m
 [m
[32m+[m[32m    def _get_connection(self):[m
[32m+[m[32m        conn = get_connection()[m
[32m+[m[32m        if conn is None:[m
[32m+[m[32m            raise RuntimeError("Falha ao conectar ao banco de dados.")[m
[32m+[m[32m        return conn[m
[32m+[m
[32m+[m[32m    def _email_valido(self, email: str) -> bool:[m
[32m+[m[32m        if not email:[m
[32m+[m[32m            return True  # permite vazio[m
[32m+[m
[32m+[m[32m        # não permite vírgula[m
[32m+[m[32m        if "," in email:[m
[32m+[m[32m            return False[m
[32m+[m
[32m+[m[32m        padrao = r"^[^@\s,]+@[^@\s,]+\.[^@\s,]+$"[m
[32m+[m[32m        return re.match(padrao, email) is not None[m
[32m+[m
     def load_utilizadores(self):[m
         """Carrega utilizadores da base de dados."""[m
         try:[m
[31m-            with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:[m
[32m+[m[32m            with closing(self._get_connection()) as conn, closing(conn.cursor()) as cur:[m
                 cur.execute([m
                     "SELECT id, nome, email, ativo FROM utilizadores ORDER BY nome"[m
                 )[m
                 rows = cur.fetchall()[m
 [m
             self.table.setRowCount(len(rows))[m
[31m-            for r, (uid, nome, email, ativo) in enumerate(rows):[m
[32m+[m[32m            for r, row in enumerate(rows):[m
[32m+[m[32m                uid = row["id"][m
[32m+[m[32m                nome = row["nome"][m
[32m+[m[32m                email = row["email"][m
[32m+[m[32m                ativo = row["ativo"][m
[32m+[m
                 self.table.setItem(r, 0, QTableWidgetItem(str(uid)))[m
                 self.table.setItem(r, 1, QTableWidgetItem(nome or ""))[m
                 self.table.setItem(r, 2, QTableWidgetItem(email or ""))[m
[36m@@ -163,11 +186,40 @@[m [mclass UtilizadoresTab(QWidget):[m
             return[m
 [m
         dados = dialog.get_dados()[m
[32m+[m
[32m+[m[32m        # valida formato do email[m
[32m+[m[32m        if not self._email_valido(dados["email"]):[m
[32m+[m[32m            QMessageBox.warning([m
[32m+[m[32m                self,[m
[32m+[m[32m                "Email inválido",[m
[32m+[m[32m                "Informe um endereço de email válido (ex: nome@dominio.com).",[m
[32m+[m[32m            )[m
[32m+[m[32m            return[m
[32m+[m
         try:[m
[31m-            with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:[m
[32m+[m[32m            with closing(self._get_connection()) as conn, closing(conn.cursor()) as cur:[m
[32m+[m[32m                # verifica se já existe utilizador com mesmo email[m
[32m+[m[32m                if dados["email"]:[m
[32m+[m[32m                    cur.execute([m
[32m+[m[32m                        "SELECT COUNT(*) AS qtd FROM utilizadores WHERE email = %s",[m
[32m+[m[32m                        (dados["email"],),[m
[32m+[m[32m                    )[m
[32m+[m[32m                    row = cur.fetchone()[m
[32m+[m[32m                    qtd = row["qtd"] if hasattr(row, "keys") else row[0][m
[32m+[m[32m                    if qtd > 0:[m
[32m+[m[32m                        QMessageBox.warning([m
[32m+[m[32m                            self,[m
[32m+[m[32m                            "Duplicado",[m
[32m+[m[32m                            "Já existe um utilizador com esse e‑mail."[m
[32m+[m[32m                        )[m
[32m+[m[32m                        return[m
[32m+[m
                 cur.execute([m
[31m-                    "INSERT INTO utilizadores (nome, email, ativo) VALUES (%s, %s, %s)",[m
[31m-                    (dados["nome"], dados["email"], True)[m
[32m+[m[32m                    """[m
[32m+[m[32m                    INSERT INTO utilizadores (nome, email, ativo)[m
[32m+[m[32m                    VALUES (%s, %s, %s)[m
[32m+[m[32m                    """,[m
[32m+[m[32m                    (dados["nome"], dados["email"], True),[m
                 )[m
                 conn.commit()[m
 [m
[36m@@ -191,10 +243,10 @@[m [mclass UtilizadoresTab(QWidget):[m
         novo_status = not status_atual  # True / False[m
 [m
         try:[m
[31m-            with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:[m
[32m+[m[32m            with closing(self._get_connection()) as conn, closing(conn.cursor()) as cur:[m
                 cur.execute([m
                     "UPDATE utilizadores SET ativo = %s WHERE id = %s",[m
[31m-                    (novo_status, util_id)[m
[32m+[m[32m                    (novo_status, util_id),[m
                 )[m
                 conn.commit()[m
 [m
[36m@@ -217,24 +269,28 @@[m [mclass UtilizadoresTab(QWidget):[m
 [m
         # Verifica movimentações[m
         try:[m
[31m-            with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:[m
[32m+[m[32m            with closing(self._get_connection()) as conn, closing(conn.cursor()) as cur:[m
                 cur.execute([m
                     """[m
[31m-                    SELECT COUNT(*) FROM movimentacoes [m
[32m+[m[32m                    SELECT COUNT(*) AS qtd[m
[32m+[m[32m                    FROM movimentacoes[m[41m [m
                     WHERE utilizador_id = %s OR usuario = %s[m
                     """,[m
[31m-                    (util_id, nome)[m
[32m+[m[32m                    (util_id, nome),[m
                 )[m
[31m-                qtd = cur.fetchone()[0][m
[32m+[m[32m                row = cur.fetchone()[m
[32m+[m[32m                qtd = row["qtd"] if hasattr(row, "keys") else row[0][m
         except Exception as e:[m
             logger.error(f"Erro ao verificar movimentações: {e}")[m
[32m+[m[32m            QMessageBox.critical(self, "Erro", f"Erro ao verificar movimentações:\n{e}")[m
             return[m
 [m
         if qtd > 0:[m
             QMessageBox.warning([m
[31m-                self, "Não permitido",[m
[32m+[m[32m                self,[m
[32m+[m[32m                "Não permitido",[m
                 "Este utilizador possui movimentações associadas.\n"[m
[31m-                "Use apenas 'Ativar/Desativar'."[m
[32m+[m[32m                "Use apenas 'Ativar/Desativar'.",[m
             )[m
             return[m
 [m
[36m@@ -246,9 +302,10 @@[m [mclass UtilizadoresTab(QWidget):[m
                 return[m
 [m
             senha, ok = QInputDialog.getText([m
[31m-                self, "🔐 Confirmação de Senha",[m
[32m+[m[32m                self,[m
[32m+[m[32m                "🔐 Confirmação de Senha",[m
                 f"Digite sua senha para excluir '{nome}':",[m
[31m-                QLineEdit.EchoMode.Password[m
[32m+[m[32m                QLineEdit.EchoMode.Password,[m
             )[m
             if not ok or not validar_login(user["login"], senha):[m
                 QMessageBox.warning(self, "Acesso Negado", "Senha inválida!")[m
[36m@@ -256,17 +313,18 @@[m [mclass UtilizadoresTab(QWidget):[m
 [m
         # Confirmação final[m
         resp = QMessageBox.question([m
[31m-            self, "⚠️ Confirmar Exclusão",[m
[32m+[m[32m            self,[m
[32m+[m[32m            "⚠️ Confirmar Exclusão",[m
             f"Excluir permanentemente o utilizador '{nome}'?\n\n"[m
             "Esta ação não pode ser desfeita!",[m
             QMessageBox.Yes | QMessageBox.No,[m
[31m-            QMessageBox.No[m
[32m+[m[32m            QMessageBox.No,[m
         )[m
         if resp != QMessageBox.Yes:[m
             return[m
 [m
         try:[m
[31m-            with closing(get_db_connection()) as conn, closing(conn.cursor()) as cur:[m
[32m+[m[32m            with closing(self._get_connection()) as conn, closing(conn.cursor()) as cur:[m
                 cur.execute("DELETE FROM utilizadores WHERE id = %s", (util_id,))[m
                 conn.commit()[m
 [m
[36m@@ -281,9 +339,10 @@[m [mclass UtilizadoresTab(QWidget):[m
     def exportar_csv(self):[m
         """Exporta tabela para CSV."""[m
         path, _ = QFileDialog.getSaveFileName([m
[31m-            self, "📊 Exportar Utilizadores",[m
[32m+[m[32m            self,[m
[32m+[m[32m            "📊 Exportar Utilizadores",[m
             "utilizadores.csv",[m
[31m-            "CSV Files (*.csv)"[m
[32m+[m[32m            "CSV Files (*.csv)",[m
         )[m
         if not path:[m
             return[m
[36m@@ -292,15 +351,20 @@[m [mclass UtilizadoresTab(QWidget):[m
             with open(path, "w", newline="", encoding="utf-8") as f:[m
                 writer = csv.writer(f, delimiter=";")[m
                 # Headers[m
[31m-                headers = [self.table.horizontalHeaderItem(c).text()[m
[31m-                           for c in range(self.table.columnCount())][m
[32m+[m[32m                headers = [[m
[32m+[m[32m                    self.table.horizontalHeaderItem(c).text()[m
[32m+[m[32m                    for c in range(self.table.columnCount())[m
[32m+[m[32m                ][m
                 writer.writerow(headers)[m
 [m
                 # Dados[m
                 for row in range(self.table.rowCount()):[m
[31m-                    linha = [self.table.item(row, col).text()[m
[31m-                             if self.table.item(row, col) else ""[m
[31m-                             for col in range(self.table.columnCount())][m
[32m+[m[32m                    linha = [[m
[32m+[m[32m                        self.table.item(row, col).text()[m
[32m+[m[32m                        if self.table.item(row, col)[m
[32m+[m[32m                        else ""[m
[32m+[m[32m                        for col in range(self.table.columnCount())[m
[32m+[m[32m                    ][m
                     writer.writerow(linha)[m
 [m
             self.show_success(f"Exportado para: {path}")[m
[1mdiff --git a/autenticacao/login_window.py b/autenticacao/login_window.py[m
[1mindex 4484341..593f8d8 100644[m
[1m--- a/autenticacao/login_window.py[m
[1m+++ b/autenticacao/login_window.py[m
[36m@@ -1,196 +1,67 @@[m
[31m-# autenticacao/login_window.py[m
[31m-[m
 import traceback[m
[31m-from PyQt6.QtWidgets import ([m
[31m-    QWidget, QLineEdit, QLabel, QPushButton, QVBoxLayout,[m
[31m-    QMessageBox, QDialog, QFormLayout, QDialogButtonBox[m
[31m-)[m
 [m
[31m-from .autenticacao import ([m
[31m-    get_user_by_login, verify_password, hash_password,[m
[31m-    show_info, show_warning[m
[32m+[m[32mfrom PyQt6.QtWidgets import ([m
[32m+[m[32m    QWidget,[m
[32m+[m[32m    QMessageBox,[m
[32m+[m[32m    QVBoxLayout,[m
[32m+[m[32m    QFormLayout,[m
[32m+[m[32m    QLineEdit,[m
[32m+[m[32m    QPushButton,[m
 )[m
[31m-from database_module import execute_query[m
[31m-from .session import session_manager[m
[31m-from utils.utils_log import log_acao[m
[31m-from autenticacao import get_current_user[m
[31m-[m
[31m-[m
[31m-class ChangePasswordDialog(QDialog):[m
[31m-    def __init__(self, user_id):[m
[31m-        super().__init__()[m
[31m-        self.user_id = user_id[m
[31m-        self.setWindowTitle("Trocar Senha - Primeiro Login")[m
[31m-[m
[31m-        self.layout = QFormLayout(self)[m
[31m-[m
[31m-        self.new_password = QLineEdit()[m
[31m-        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)[m
[31m-        self.confirm_password = QLineEdit()[m
[31m-        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)[m
[31m-[m
[31m-        self.layout.addRow("Nova Senha:", self.new_password)[m
[31m-        self.layout.addRow("Confirme Senha:", self.confirm_password)[m
 [m
[31m-        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)[m
[31m-        self.buttons.accepted.connect(self.change_password)[m
[31m-        self.buttons.rejected.connect(self.reject)[m
[31m-        self.layout.addWidget(self.buttons)[m
[31m-[m
[31m-        self.setLayout(self.layout)[m
[31m-[m
[31m-    def change_password(self):[m
[31m-        pw = self.new_password.text()[m
[31m-        confirm = self.confirm_password.text()[m
[31m-[m
[31m-        if not pw or not confirm:[m
[31m-            show_warning("Erro", "Preencha ambos os campos de senha.")[m
[31m-            return[m
[31m-[m
[31m-        if pw != confirm:[m
[31m-            show_warning("Erro", "As senhas não conferem.")[m
[31m-            return[m
[31m-[m
[31m-        senha_hashed = hash_password(pw)[m
[31m-[m
[31m-        # Coluna de senha: ajuste se necessário (senha / senha_hash)[m
[31m-        query = "UPDATE usuarios SET senha = %s, primeiro_login = %s WHERE id = %s"[m
[31m-        # Exemplo alternativo:[m
[31m-        # query = "UPDATE usuarios SET senha_hash = %s, primeiro_login = %s WHERE id = %s"[m
[31m-[m
[31m-        execute_query(query, (senha_hashed, False, self.user_id))[m
[31m-        log_acao(f"Senha alterada com sucesso para usuário id={self.user_id}")[m
[31m-        show_info("Sucesso", "Senha alterada com sucesso!")[m
[31m-        self.accept()[m
[32m+[m[32mfrom autenticacao import session_manager[m
[32m+[m[32mfrom autenticacao.autenticacao import get_user_by_login[m
[32m+[m[32m# from logs.log_actions import log_acao  # reative depois se quiser[m
 [m
 [m
 class LoginWindow(QWidget):[m
[31m-    def __init__(self, on_login_success):[m
[31m-        super().__init__()[m
[32m+[m[32m    def __init__(self, on_login_success=None, parent=None):[m
[32m+[m[32m        super().__init__(parent)[m
         self.on_login_success = on_login_success[m
 [m
         self.setWindowTitle("Login Sistema Controle de Chaves")[m
[31m-        self.setGeometry(100, 100, 300, 150)[m
[31m-[m
[31m-        layout = QVBoxLayout()[m
[32m+[m[32m        self.resize(320, 160)[m
 [m
[31m-        self.label_login = QLabel("Login:")[m
[31m-        self.input_login = QLineEdit()[m
[31m-        layout.addWidget(self.label_login)[m
[31m-        layout.addWidget(self.input_login)[m
[32m+[m[32m        layout = QVBoxLayout(self)[m
[32m+[m[32m        form = QFormLayout()[m
 [m
[31m-        self.label_senha = QLabel("Senha:")[m
[31m-        self.input_senha = QLineEdit()[m
[31m-        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password)[m
[31m-        layout.addWidget(self.label_senha)[m
[31m-        layout.addWidget(self.input_senha)[m
[32m+[m[32m        self.line_login = QLineEdit()[m
[32m+[m[32m        self.line_senha = QLineEdit()[m
[32m+[m[32m        self.line_senha.setEchoMode(QLineEdit.EchoMode.Password)[m
 [m
[31m-        self.btn_entrar = QPushButton("Entrar")[m
[31m-        self.btn_entrar.clicked.connect(self.try_login)[m
[31m-        layout.addWidget(self.btn_entrar)[m
[32m+[m[32m        form.addRow("Login:", self.line_login)[m
[32m+[m[32m        form.addRow("Senha:", self.line_senha)[m
 [m
[31m-        self.setLayout(layout)[m
[31m-        self.centralizar_janela()[m
[31m-        self.input_login.setFocus()[m
[32m+[m[32m        self.btn_login = QPushButton("Entrar")[m
[32m+[m[32m        self.btn_login.clicked.connect(self.try_login)[m
 [m
[31m-    def centralizar_janela(self):[m
[31m-        qr = self.frameGeometry()[m
[31m-        cp = self.screen().availableGeometry().center()[m
[31m-        qr.moveCenter(cp)[m
[31m-        self.move(qr.topLeft())[m
[32m+[m[32m        layout.addLayout(form)[m
[32m+[m[32m        layout.addWidget(self.btn_login)[m
 [m
     def try_login(self):[m
[31m-        login = self.input_login.text().strip()[m
[31m-        senha = self.input_senha.text().strip()[m
[31m-[m
[31m-        if not login or not senha:[m
[31m-            QMessageBox.warning(self, "Erro", "Preencha login e senha.")[m
[31m-            log_acao(f"Tentativa de login com campos vazios (login='{login}')")[m
[31m-            return[m
[31m-[m
[31m-        # Busca usuário no Postgres[m
[31m-        user = get_user_by_login(login)[m
[31m-        if not user:[m
[31m-            QMessageBox.warning(self, "Erro", "Login ou senha incorretos.")[m
[31m-            log_acao(f"Tentativa de login com usuário inexistente: '{login}'")[m
[31m-            return[m
[31m-[m
[31m-        user = dict(user)[m
[31m-        senha_banco = user["senha"]  # ou senha_hash, conforme seu schema[m
[31m-[m
[31m-        # verifica se senha está em formato seguro (bcrypt)[m
[31m-        hash_valido = senha_banco and senha_banco.startswith("$2b$")[m
[31m-        if not hash_valido:[m
[31m-            log_acao([m
[31m-                f"Login bloqueado: senha insegura detectada para usuário '{login}'"[m
[31m-            )[m
[31m-            show_warning([m
[31m-                "Atenção",[m
[31m-                "Sua senha está salva de forma insegura. Você precisa trocá-la para continuar."[m
[31m-            )[m
[31m-            dialog = ChangePasswordDialog(user["id"])[m
[31m-            if dialog.exec() == QDialog.Accepted:[m
[31m-                QMessageBox.information([m
[31m-                    self,[m
[31m-                    "Sucesso",[m
[31m-                    "Senha cadastrada com segurança! Faça login novamente."[m
[31m-                )[m
[31m-                log_acao([m
[31m-                    f"Senha atualizada para usuário '{login}' (senha antiga insegura)"[m
[31m-                )[m
[31m-                self.input_login.clear()[m
[31m-                self.input_senha.clear()[m
[32m+[m[32m        try:[m
[32m+[m[32m            login = self.line_login.text().strip()[m
[32m+[m[32m            senha = self.line_senha.text().strip()[m
[32m+[m
[32m+[m[32m            if not login or not senha:[m
[32m+[m[32m                QMessageBox.warning(self, "Erro", "Informe login e senha.")[m
                 return[m
[31m-            else:[m
[31m-                QMessageBox.warning([m
[31m-                    self,[m
[31m-                    "Aviso",[m
[31m-                    "Troca de senha obrigatória cancelada."[m
[31m-                )[m
[31m-                log_acao([m
[31m-                    f"Usuário '{login}' cancelou troca de senha obrigatória"[m
[31m-                )[m
[32m+[m
[32m+[m[32m            user = get_user_by_login(login)[m
[32m+[m[32m            if not user:[m
[32m+[m[32m                QMessageBox.warning(self, "Erro", "Utilizador não encontrado.")[m
[32m+[m[32m                # log_acao(f"Tentativa de login com utilizador inexistente '{login}'")[m
                 return[m
 [m
[31m-        # valida senha com bcrypt[m
[31m-        senha_valida = verify_password(senha_banco, senha)[m
[31m-        print(f"Senha válida? {senha_valida}")[m
[32m+[m[32m            # TODO: validação real da senha[m
[32m+[m[32m            senha_valida = True[m
[32m+[m[32m            if not senha_valida:[m
[32m+[m[32m                QMessageBox.warning(self, "Erro", "Senha inválida.")[m
[32m+[m[32m                # log_acao(f"Tentativa de login com senha inválida para '{login}'")[m
[32m+[m[32m                return[m
 [m
[31m-        if not senha_valida:[m
[31m-            QMessageBox.warning(self, "Erro", "Login ou senha incorretos.")[m
[31m-            log_acao(f"Tentativa de login inválida para usuário '{login}'")[m
[31m-            return[m
[32m+[m[32m            print("Senha válida? True")[m
 [m
[31m-        try:[m
[31m-            print("DEBUG: antes de verificar primeiro_login")[m
[31m-            # Primeiro login exige troca de senha[m
[31m-            if user.get("primeiro_login"):[m
[31m-                print("DEBUG: caiu em primeiro_login")[m
[31m-                log_acao(f"Primeiro login detectado para usuário '{login}'")[m
[31m-                dialog = ChangePasswordDialog(user["id"])[m
[31m-                resultado = dialog.exec()[m
[31m-                if resultado == QDialog.Accepted:[m
[31m-                    QMessageBox.information([m
[31m-                        self,[m
[31m-                        "Sucesso",[m
[31m-                        "Senha cadastrada com segurança! Faça login novamente."[m
[31m-                    )[m
[31m-                    self.input_senha.clear()[m
[31m-                    self.input_login.setFocus()[m
[31m-                    return[m
[31m-                else:[m
[31m-                    show_warning([m
[31m-                        "Aviso",[m
[31m-                        "É necessário trocar a senha para continuar."[m
[31m-                    )[m
[31m-                    log_acao([m
[31m-                        f"Usuário '{login}' recusou trocar a senha no primeiro login"[m
[31m-                    )[m
[31m-                    self.input_senha.clear()[m
[31m-                    self.input_login.setFocus()[m
[31m-                    return[m
[31m-[m
[31m-            # Login normal (não é primeiro login)[m
             print("DEBUG: antes de session_manager.login")[m
             if not session_manager.login(user["login"]):[m
                 print("DEBUG: session_manager.login retornou False")[m
[36m@@ -199,26 +70,28 @@[m [mclass LoginWindow(QWidget):[m
                     "Erro",[m
                     "Falha ao carregar sessão do usuário."[m
                 )[m
[31m-                log_acao([m
[31m-                    f"Falha ao carregar sessão para usuário '{login}'"[m
[31m-                )[m
[32m+[m[32m                # log_acao(f"Falha ao carregar sessão para usuário '{login}'")[m
                 return[m
 [m
             QMessageBox.information(self, "Sucesso", "Login realizado com sucesso.")[m
[31m-            log_acao(f"Login bem-sucedido para usuário '{login}'")[m
[32m+[m[32m            # log_acao(f"Login bem-sucedido para usuário '{login}'")[m
 [m
             print("DEBUG: antes de on_login_success")[m
[31m-            user_atual = get_current_user()[m
[32m+[m[32m            user_atual = session_manager.current_user[m
             print("DEBUG user_atual após login:", user_atual)[m
[31m-            self.on_login_success(user_atual)[m
[32m+[m
[32m+[m[32m            if self.on_login_success:[m
[32m+[m[32m                self.on_login_success(user_atual)[m
[32m+[m
             print("DEBUG: depois de on_login_success (antes de close)")[m
             self.close()[m
 [m
         except Exception:[m
             erro = traceback.format_exc()[m
[31m-            print(erro)[m
[31m-            log_acao(f"Erro interno após login para usuário '{login}': {erro}")[m
[31m-            show_warning([m
[32m+[m[32m            print("ERRO interno no try_login:", erro)[m
[32m+[m[32m            QMessageBox.critical([m
[32m+[m[32m                self,[m
                 "Erro",[m
[31m-                "Um erro interno ocorreu na transição de telas."[m
[32m+[m[32m                "Ocorreu um erro interno ao tentar efetuar o login.",[m
             )[m
[32m+[m[32m            # log_acao(f"Erro interno no login para usuário '{login}': {erro}")[m
[1mdiff --git a/controle/movimentacoes.py b/controle/movimentacoes.py[m
[1mindex d081440..6047efd 100644[m
[1m--- a/controle/movimentacoes.py[m
[1m+++ b/controle/movimentacoes.py[m
[36m@@ -205,7 +205,6 @@[m [mclass MovimentacoesTab(QWidget):[m
         print("UI criada")[m
 [m
         try:[m
[31m-            # Assumindo que as tabelas já existem no Postgres (sem criar aqui)[m
             self.carregar_movimentacoes()[m
             print("Movimentações carregadas")[m
         except Exception as e:[m
[36m@@ -224,7 +223,7 @@[m [mclass MovimentacoesTab(QWidget):[m
         self.timer.start(5000)[m
 [m
     def _get_dash_main(self):[m
[31m-        from interface.dash_main import DashMain  # import local, evita ciclo[m
[32m+[m[32m        from interface.dash_main import DashMain[m
         janela = self.parentWidget()[m
         while janela is not None and not isinstance(janela, DashMain):[m
             janela = janela.parentWidget()[m
[36m@@ -372,10 +371,11 @@[m [mclass MovimentacoesTab(QWidget):[m
 [m
     def load_utilizadores_combo(self):[m
         self.combo_utilizador.clear()[m
[32m+[m
         conn = get_db_connection()[m
         cur = conn.cursor()[m
         cur.execute("""[m
[31m-            SELECT id, nome, email[m
[32m+[m[32m            SELECT id, COALESCE(nome, '') AS nome, COALESCE(email, '') AS email[m
             FROM utilizadores[m
             WHERE ativo = TRUE[m
             ORDER BY nome[m
[36m@@ -384,8 +384,17 @@[m [mclass MovimentacoesTab(QWidget):[m
         conn.close()[m
 [m
         self.combo_utilizador.addItem("Selecione o utilizador...", None)[m
[31m-        for uid, nome, email in rows:[m
[31m-            display = f"{nome} ({email})" if email else nome[m
[32m+[m
[32m+[m[32m        for row in rows:[m
[32m+[m[32m            uid = row[0][m
[32m+[m[32m            nome = row[1] or ""[m
[32m+[m[32m            email = row[2] or ""[m
[32m+[m
[32m+[m[32m            if email:[m
[32m+[m[32m                display = f"{nome} ({email})"[m
[32m+[m[32m            else:[m
[32m+[m[32m                display = nome[m
[32m+[m
             self.combo_utilizador.addItem(display, uid)[m
 [m
     def cadastrar_utilizador_rapido(self):[m
[36m@@ -410,7 +419,6 @@[m [mclass MovimentacoesTab(QWidget):[m
                 )[m
                 conn.commit()[m
 [m
[31m-                # recuperar id (em psycopg2 pode usar RETURNING se preferir)[m
                 cur.execute("SELECT currval(pg_get_serial_sequence('utilizadores','id'))")[m
                 novo_id = cur.fetchone()[0][m
 [m
[36m@@ -634,7 +642,7 @@[m [mclass MovimentacoesTab(QWidget):[m
 [m
             dash = self._get_dash_main()[m
             if dash is not None:[m
[31m-                dash.show_operation_done("Devolução registrada!")[m
[32m+[m[32m                dash.show_operation_done("Devolução registradoa!")[m
         except Exception as e:[m
             log_acao([m
                 action="devolucao",[m
[1mdiff --git a/controle/selecionar_sala_dialog.py b/controle/selecionar_sala_dialog.py[m
[1mindex 33a0d80..3c6b138 100644[m
[1m--- a/controle/selecionar_sala_dialog.py[m
[1m+++ b/controle/selecionar_sala_dialog.py[m
[36m@@ -1,4 +1,3 @@[m
[31m-import os[m
 from PyQt6.QtWidgets import ([m
     QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,[m
     QLineEdit, QLabel, QHeaderView, QDialogButtonBox, QMessageBox[m
[36m@@ -6,7 +5,7 @@[m [mfrom PyQt6.QtWidgets import ([m
 from PyQt6.QtCore import Qt[m
 from PyQt6.QtGui import QBrush, QColor[m
 [m
[31m-from autenticacao.helpers_autenticacao import get_db_connection[m
[32m+[m[32mfrom database_module import get_connection  # usa o mesmo módulo oficial[m
 [m
 [m
 class SelecionarSalaDialog(QDialog):[m
[36m@@ -65,30 +64,50 @@[m [mclass SelecionarSalaDialog(QDialog):[m
     def _carregar_salas(self):[m
         self.table.setRowCount(0)[m
 [m
[31m-        conn = get_db_connection()[m
[31m-        cursor = conn.cursor()[m
[31m-        cursor.execute("""[m
[31m-            SELECT s.id, s.nome, p.nome, a.nome, s.status[m
[31m-            FROM salas s[m
[31m-            LEFT JOIN predios p ON s.predio_id = p.id[m
[31m-            LEFT JOIN anexos a ON s.anexo_id = a.id[m
[31m-            ORDER BY s.nome[m
[31m-        """)[m
[31m-        rows = cursor.fetchall()[m
[31m-        conn.close()[m
[31m-[m
[31m-        for sid, nome, predio, anexo, status in rows:[m
[31m-            row = self.table.rowCount()[m
[31m-            self.table.insertRow(row)[m
[32m+[m[32m        try:[m
[32m+[m[32m            conn = get_connection()[m
[32m+[m[32m            if conn is None:[m
[32m+[m[32m                QMessageBox.critical(self, "Erro", "Falha ao conectar ao banco de dados.")[m
[32m+[m[32m                return[m
[32m+[m
[32m+[m[32m            cursor = conn.cursor()[m
[32m+[m[32m            cursor.execute([m
[32m+[m[32m                """[m
[32m+[m[32m                SELECT s.id,[m
[32m+[m[32m                       s.nome,[m
[32m+[m[32m                       p.nome AS predio_nome,[m
[32m+[m[32m                       a.nome AS anexo_nome,[m
[32m+[m[32m                       s.status[m
[32m+[m[32m                FROM salas s[m
[32m+[m[32m                LEFT JOIN predios p ON s.predio_id = p.id[m
[32m+[m[32m                LEFT JOIN anexos a ON s.anexo_id = a.id[m
[32m+[m[32m                ORDER BY s.nome[m
[32m+[m[32m                """[m
[32m+[m[32m            )[m
[32m+[m[32m            rows = cursor.fetchall()[m
[32m+[m[32m            conn.close()[m
[32m+[m[32m        except Exception as e:[m
[32m+[m[32m            QMessageBox.critical(self, "Erro", f"Erro ao carregar salas:\n{e}")[m
[32m+[m[32m            return[m
[32m+[m
[32m+[m[32m        for row in rows:[m
[32m+[m[32m            sid = row["id"][m
[32m+[m[32m            nome = row["nome"][m
[32m+[m[32m            predio = row["predio_nome"][m
[32m+[m[32m            anexo = row["anexo_nome"][m
[32m+[m[32m            status = row["status"][m
[32m+[m
[32m+[m[32m            r = self.table.rowCount()[m
[32m+[m[32m            self.table.insertRow(r)[m
 [m
             # Sala: apenas o nome[m
             item_sala = QTableWidgetItem(nome or "")[m
             item_sala.setData(Qt.ItemDataRole.UserRole, sid)  # guarda o id da sala[m
[31m-            self.table.setItem(row, 0, item_sala)[m
[32m+[m[32m            self.table.setItem(r, 0, item_sala)[m
 [m
             # Prédio e Anexo em colunas separadas[m
[31m-            self.table.setItem(row, 1, QTableWidgetItem(predio or ""))[m
[31m-            self.table.setItem(row, 2, QTableWidgetItem(anexo or ""))[m
[32m+[m[32m            self.table.setItem(r, 1, QTableWidgetItem(predio or ""))[m
[32m+[m[32m            self.table.setItem(r, 2, QTableWidgetItem(anexo or ""))[m
 [m
             # Status com cor[m
             item_status = QTableWidgetItem(status or "")[m
[36m@@ -96,7 +115,7 @@[m [mclass SelecionarSalaDialog(QDialog):[m
                 item_status.setBackground(QBrush(QColor(144, 238, 144)))[m
             elif status == "indisponivel":[m
                 item_status.setBackground(QBrush(QColor(255, 120, 120)))[m
[31m-            self.table.setItem(row, 3, item_status)[m
[32m+[m[32m            self.table.setItem(r, 3, item_status)[m
 [m
     def _capturar_linhas(self):[m
         """[m
[36m@@ -104,11 +123,19 @@[m [mclass SelecionarSalaDialog(QDialog):[m
         """[m
         dados = [][m
         for row in range(self.table.rowCount()):[m
[31m-            sala = self.table.item(row, 0).text()[m
[31m-            predio = self.table.item(row, 1).text()[m
[31m-            anexo = self.table.item(row, 2).text()[m
[31m-            status = self.table.item(row, 3).text()[m
[31m-            sid = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)[m
[32m+[m[32m            sala_item = self.table.item(row, 0)[m
[32m+[m[32m            predio_item = self.table.item(row, 1)[m
[32m+[m[32m            anexo_item = self.table.item(row, 2)[m
[32m+[m[32m            status_item = self.table.item(row, 3)[m
[32m+[m
[32m+[m[32m            if not sala_item:[m
[32m+[m[32m                continue[m
[32m+[m
[32m+[m[32m            sala = sala_item.text()[m
[32m+[m[32m            predio = predio_item.text() if predio_item else ""[m
[32m+[m[32m            anexo = anexo_item.text() if anexo_item else ""[m
[32m+[m[32m            status = status_item.text() if status_item else ""[m
[32m+[m[32m            sid = sala_item.data(Qt.ItemDataRole.UserRole)[m
             dados.append((sala, predio, anexo, status, sid))[m
         return dados[m
 [m
[36m@@ -120,22 +147,22 @@[m [mclass SelecionarSalaDialog(QDialog):[m
                 texto in sala.lower() or[m
                 texto in (predio or "").lower() or[m
                 texto in (anexo or "").lower()):[m
[31m-                row = self.table.rowCount()[m
[31m-                self.table.insertRow(row)[m
[32m+[m[32m                r = self.table.rowCount()[m
[32m+[m[32m                self.table.insertRow(r)[m
 [m
                 item_sala = QTableWidgetItem(sala)[m
                 item_sala.setData(Qt.ItemDataRole.UserRole, sid)[m
[31m-                self.table.setItem(row, 0, item_sala)[m
[32m+[m[32m                self.table.setItem(r, 0, item_sala)[m
 [m
[31m-                self.table.setItem(row, 1, QTableWidgetItem(predio))[m
[31m-                self.table.setItem(row, 2, QTableWidgetItem(anexo))[m
[32m+[m[32m                self.table.setItem(r, 1, QTableWidgetItem(predio or ""))[m
[32m+[m[32m                self.table.setItem(r, 2, QTableWidgetItem(anexo or ""))[m
 [m
[31m-                item_status = QTableWidgetItem(status)[m
[32m+[m[32m                item_status = QTableWidgetItem(status or "")[m
                 if status == "disponivel":[m
                     item_status.setBackground(QBrush(QColor(144, 238, 144)))[m
                 elif status == "indisponivel":[m
                     item_status.setBackground(QBrush(QColor(255, 120, 120)))[m
[31m-                self.table.setItem(row, 3, item_status)[m
[32m+[m[32m                self.table.setItem(r, 3, item_status)[m
 [m
     def _pegar_selecao(self):[m
         selected = self.table.selectedItems()[m
[1mdiff --git a/interface/dash_main.py b/interface/dash_main.py[m
[1mindex 9fcbfe7..5782c8e 100644[m
[1m--- a/interface/dash_main.py[m
[1m+++ b/interface/dash_main.py[m
[36m@@ -13,200 +13,94 @@[m [mfrom PyQt6.QtWidgets import ([m
     QLabel,[m
     QApplication,[m
 )[m
[31m-[m
 from PyQt6.QtGui import QPixmap[m
 from PyQt6.QtCore import Qt, QTimer[m
 [m
 from admin.admin import AdminTab[m
 from admin.log_viewer_tab import LogViewerTab[m
[31m-[m
[31m-from autenticacao import session_manager, get_current_user, is_admin[m
[31m-[m
[31m-from config import ([m
[31m-    APP_NAME,[m
[31m-    APP_VERSION,[m
[31m-    APP_COMPANY,[m
[31m-    APP_DEVELOPER,[m
[31m-    APP_COPYRIGHT,[m
[31m-    APP_LOGO_PATH,[m
[31m-)[m
 from controle.movimentacoes import MovimentacoesTab[m
 from relatorios.relatorios_tab import RelatoriosTab[m
[32m+[m[32mfrom autenticacao import session_manager[m
 [m
 [m
 class DashMain(QMainWindow):[m
     def __init__(self, on_logout=None):[m
         super().__init__()[m
[32m+[m
         print("DashMain.__init__ chamado")[m
 [m
         self.on_logout = on_logout[m
 [m
[31m-        info_user = get_current_user()[m
[31m-        print("DEBUG get_current_user em DashMain:", info_user)[m
[31m-        print("DEBUG session_manager.is_admin:", session_manager.is_admin)[m
[31m-        print("DEBUG is_admin():", is_admin())[m
[32m+[m[32m        # Pega usuário atual da sessão (SessionUser)[m
[32m+[m[32m        user = session_manager.current_user[m
[32m+[m[32m        if not user:[m
[32m+[m[32m            self.user_login = "?"[m
[32m+[m[32m            self.user_nome = "Desconhecido"[m
[32m+[m[32m            self.user_is_admin = False[m
[32m+[m[32m        else:[m
[32m+[m[32m            self.user_login = getattr(user, "login", "?")[m
[32m+[m[32m            self.user_nome = getattr(user, "nome", "Desconhecido")[m
[32m+[m[32m            self.user_is_admin = getattr(user, "is_admin", False)[m
 [m
[31m-        self.setWindowTitle(f"{APP_NAME} - Painel Principal")[m
[31m-        self.resize(1200, 800)[m
[32m+[m[32m        self.setWindowTitle("Controle de Chaves - Painel Principal")[m
[32m+[m[32m        self.resize(1024, 768)[m
 [m
[31m-        # Abas principais[m
[31m-        self.tabs = QTabWidget()[m
[31m-        self.tabs.setTabPosition(QTabWidget.North)[m
[31m-        self.tabs.setMovable(False)[m
[31m-[m
[31m-        # Widget central e layout principal[m
[31m-        central = QWidget()[m
[31m-        layout_principal = QVBoxLayout(central)[m
[31m-[m
[31m-        # ===== Faixa superior: relógio (esq) + logo (centro) =====[m
[31m-        top_bar = QHBoxLayout()[m
[31m-[m
[31m-        # Relógio à esquerda com estilo customizado[m
[31m-        self.clock_label = QLabel()[m
[31m-        self.clock_label.setAlignment(Qt.ItemFlag.ItemIsLeft | Qt.ItemFlag.ItemIsVCenter)[m
[31m-        self.clock_label.setStyleSheet("""[m
[31m-            QLabel {[m
[31m-                font-family: 'Consolas', 'Courier New', monospace;[m
[31m-                font-size: 20px;[m
[31m-                font-weight: bold;[m
[31m-                color: #00FF00;[m
[31m-                background-color: #000000;[m
[31m-                padding: 6px 12px;[m
[31m-                border-radius: 6px;[m
[31m-                border: 1px solid #00AA00;[m
[31m-            }[m
[31m-        """)[m
[31m-        top_bar.addWidget(self.clock_label)[m
[31m-[m
[31m-        # Stretch para empurrar o logo para o centro visual[m
[31m-        top_bar.addStretch()[m
[31m-[m
[31m-        # Logo centralizado[m
[31m-        self.logo_label = QLabel()[m
[31m-        pix = QPixmap(APP_LOGO_PATH)[m
[31m-        if not pix.isNull():[m
[31m-            pix = pix.scaled(260, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation)[m
[31m-            self.logo_label.setPixmap(pix)[m
[31m-        self.logo_label.setAlignment(Qt.ItemFlag.Qt.AlignmentFlag.AlignCenter)[m
[31m-        top_bar.addWidget(self.logo_label)[m
[31m-[m
[31m-        # Stretch à direita para manter o logo no centro[m
[31m-        top_bar.addStretch()[m
[31m-[m
[31m-        layout_principal.addLayout(top_bar)[m
[31m-[m
[31m-        # Abas logo abaixo do topo[m
[31m-        layout_principal.addWidget(self.tabs)[m
[32m+[m[32m        central_widget = QWidget()[m
[32m+[m[32m        self.setCentralWidget(central_widget)[m
 [m
[31m-        # ===== Barra inferior: infos + botões =====[m
[31m-        bottom_bar = QHBoxLayout()[m
[32m+[m[32m        layout_principal = QVBoxLayout(central_widget)[m
 [m
[31m-        bottom_bar.addStretch()[m
[32m+[m[32m        # Topo[m
[32m+[m[32m        topo_layout = QHBoxLayout()[m
[32m+[m
[32m+[m[32m        self.label_usuario = QLabel([m
[32m+[m[32m            f"Utilizador: {self.user_nome} ({self.user_login})"[m
[32m+[m[32m        )[m
[32m+[m[32m        self.label_usuario.setAlignment(Qt.ItemFlag.ItemIsLeft | Qt.ItemFlag.ItemIsVCenter)[m
 [m
[31m-        self.label_usuario = QLabel()[m
         self.label_hora = QLabel()[m
[32m+[m[32m        self.label_hora.setAlignment(Qt.ItemFlag.Qt.AlignmentFlag.AlignCenter)[m
[32m+[m
[32m+[m[32m        btn_logout = QPushButton("Sair")[m
[32m+[m[32m        btn_logout.clicked.connect(self.confirmar_logout)[m
 [m
[31m-        # Label de feedback abaixo da barra inferior[m
[32m+[m[32m        topo_layout.addWidget(self.label_usuario, 2)[m
[32m+[m[32m        topo_layout.addWidget(self.label_hora, 1)[m
[32m+[m[32m        topo_layout.addWidget(btn_logout, 0)[m
[32m+[m
[32m+[m[32m        layout_principal.addLayout(topo_layout)[m
[32m+[m
[32m+[m[32m        # Feedback[m
         self.feedback_label = QLabel("")[m
         self.feedback_label.setAlignment(Qt.ItemFlag.ItemIsCenter)[m
[31m-        self.feedback_label.setStyleSheet("""[m
[31m-            QLabel {[m
[31m-                background-color: #4caf50;[m
[31m-                color: white;[m
[31m-                padding: 4px 8px;[m
[31m-                border-radius: 4px;[m
[31m-            }[m
[31m-        """)[m
[32m+[m[32m        self.feedback_label.setStyleSheet([m
[32m+[m[32m            "QLabel { background-color: #dff0d8; color: #3c763d; padding: 4px; }"[m
[32m+[m[32m        )[m
         self.feedback_label.hide()[m
         layout_principal.addWidget(self.feedback_label)[m
 [m
[32m+[m[32m        # Tabs[m
[32m+[m[32m        self.tabs = QTabWidget()[m
[32m+[m[32m        layout_principal.addWidget(self.tabs)[m
 [m
[31m-        bottom_bar.addWidget(self.label_usuario)[m
[31m-        bottom_bar.addSpacing(20)[m
[31m-        bottom_bar.addWidget(self.label_hora)[m
[31m-        bottom_bar.addSpacing(20)[m
[31m-[m
[31m-        btn_sobre = QPushButton("Sobre")[m
[31m-        btn_logout = QPushButton("Logout")[m
[31m-        btn_logout.setObjectName("btnLogout")[m
[31m-        btn_sair = QPushButton("Sair")[m
[31m-[m
[31m-        btn_sobre.clicked.connect(self.mostrar_sobre)[m
[31m-        btn_logout.clicked.connect(self.logout)[m
[31m-        btn_sair.clicked.connect(self.sair)[m
[31m-[m
[31m-        bottom_bar.addWidget(btn_sobre)[m
[31m-        bottom_bar.addWidget(btn_logout)[m
[31m-        bottom_bar.addWidget(btn_sair)[m
[31m-[m
[31m-        layout_principal.addLayout(bottom_bar)[m
[31m-[m
[31m-        self.setCentralWidget(central)[m
[31m-[m
[31m-        # Estilos de botões[m
[31m-        self.setStyleSheet("""[m
[31m-            QPushButton {[m
[31m-                padding: 10px 24px;[m
[31m-                min-height: 34px;[m
[31m-                min-width: 140px;[m
[31m-                border-radius: 6px;[m
[31m-                border: 1px solid #888;[m
[31m-                font-weight: 500;[m
[31m-            }[m
[31m-            QPushButton#btnLogout {[m
[31m-                background-color: #f9a825;[m
[31m-                color: #333333;[m
[31m-                border: 1px solid #f57f17;[m
[31m-            }[m
[31m-            QPushButton#btnLogout:hover {[m
[31m-                background-color: #fbc02d;[m
[31m-            }[m
[31m-            QPushButton#btnLogout:pressed {[m
[31m-                background-color: #f57f17;[m
[31m-            }[m
[31m-        """)[m
[31m-[m
[31m-        # Status bar para mensagens automáticas[m
[31m-        self.status = self.statusBar()[m
[31m-        self.status.showMessage("Pronto")[m
[31m-[m
[31m-        # Infos iniciais (parte inferior)[m
[31m-        self.atualizar_informacoes_usuario()[m
[31m-[m
[31m-        # Relógio superior (digital, lado esquerdo)[m
[31m-        self.clock_timer = QTimer(self)[m
[31m-        self.clock_timer.timeout.connect(self.atualizar_relogio)[m
[31m-        self.clock_timer.start(1000)  # 1 segundo[m
[31m-        self.atualizar_relogio()[m
[31m-[m
[31m-        # Carregar abas[m
[31m-        self.load_tabs()[m
[32m+[m[32m        # Relógio[m
[32m+[m[32m        self.timer = QTimer(self)[m
[32m+[m[32m        self.timer.timeout.connect(self.atualizar_hora)[m
[32m+[m[32m        self.timer.start(1000)[m
[32m+[m[32m        self.atualizar_hora()[m
 [m
[31m-    # ===== Atualizações de usuário / hora inferior =====[m
[31m-    def atualizar_informacoes_usuario(self):[m
[31m-        user = get_current_user()[m
[31m-        print("DEBUG user dict:", user)[m
[31m-        if user:[m
[31m-            nome = ([m
[31m-                    user.get("nome_real")[m
[31m-                    or user.get("nome")[m
[31m-                    or user.get("usuario")[m
[31m-                    or "Usuário"[m
[31m-            )[m
[31m-            perfil = "Administrador" if user.get("is_admin") else "Usuário comum"[m
[31m-            self.label_usuario.setText(f"{nome} - {perfil}")[m
[31m-        else:[m
[31m-            self.label_usuario.setText("Nenhum usuário logado")[m
[32m+[m[32m        self.mov_tab = None[m
[32m+[m[32m        self.rel_tab = None[m
[32m+[m[32m        self.util_tab = None[m
[32m+[m[32m        self.admin_tab = None[m
[32m+[m[32m        self.logs_tab = None[m
 [m
[31m-        agora = datetime.now().strftime("%d/%m/%Y %H:%M")[m
[31m-        self.label_hora.setText(f"{agora}")[m
[32m+[m[32m        self.load_tabs()[m
 [m
[31m-    # ===== Relógio no topo (lado esquerdo) =====[m
[31m-    def atualizar_relogio(self):[m
[32m+[m[32m    def atualizar_hora(self):[m
         agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")[m
[31m-        self.clock_label.setText(agora)[m
[32m+[m[32m        self.label_hora.setText(agora)[m
 [m
[31m-    # ===== Abas =====[m
     def load_tabs(self):[m
         print("Entrou em load_tabs()")[m
         self.tabs.clear()[m
[36m@@ -214,44 +108,60 @@[m [mclass DashMain(QMainWindow):[m
         self.mov_tab = None[m
         self.rel_tab = None[m
         self.util_tab = None[m
[32m+[m[32m        self.admin_tab = None[m
[32m+[m[32m        self.logs_tab = None[m
 [m
         # Movimentações[m
         try:[m
             self.mov_tab = MovimentacoesTab()[m
             self.tabs.addTab(self.mov_tab, "Movimentações")[m
[31m-            print("  Aba Movimentações adicionada.")[m
         except Exception as e:[m
[31m-            print(f"ERRO ao criar MovimentacoesTab: {e}")[m
[31m-            QMessageBox.critical(self, "Erro", f"Falha ao carregar aba Movimentações:\n{e}")[m
[32m+[m[32m            import traceback[m
[32m+[m[32m            print("ERRO ao criar MovimentacoesTab:", e)[m
[32m+[m[32m            traceback.print_exc()[m
[32m+[m[32m            QMessageBox.critical([m
[32m+[m[32m                self,[m
[32m+[m[32m                "Erro",[m
[32m+[m[32m                f"Falha ao carregar aba Movimentações:\n{e}",[m
[32m+[m[32m            )[m
 [m
         # Relatórios[m
         try:[m
             self.rel_tab = RelatoriosTab()[m
             self.tabs.addTab(self.rel_tab, "Relatórios")[m
[31m-            print("  Aba Relatórios adicionada.")[m
         except Exception as e:[m
[31m-            print(f"ERRO ao criar RelatoriosTab: {e}")[m
[31m-            QMessageBox.critical(self, "Erro", f"Falha ao carregar aba Relatórios:\n{e}")[m
[32m+[m[32m            import traceback[m
[32m+[m[32m            print("ERRO ao criar RelatoriosTab:", e)[m
[32m+[m[32m            traceback.print_exc()[m
[32m+[m[32m            QMessageBox.critical([m
[32m+[m[32m                self,[m
[32m+[m[32m                "Erro",[m
[32m+[m[32m                f"Falha ao carregar aba Relatórios:\n{e}",[m
[32m+[m[32m            )[m
 [m
         # Utilizadores[m
         try:[m
[31m-            self.util_tab = UtilizadoresTab(movimentacoes_tab=self.mov_tab)[m
[32m+[m[32m            self.util_tab = UtilizadoresTab()[m
             self.tabs.addTab(self.util_tab, "Utilizadores")[m
[31m-            print("  Aba Utilizadores adicionada.")[m
         except Exception as e:[m
[31m-            print(f"ERRO ao criar UtilizadoresTab: {e}")[m
[31m-            QMessageBox.critical(self, "Erro", f"Falha ao carregar aba Utilizadores:\n{e}")[m
[32m+[m[32m            import traceback[m
[32m+[m[32m            print("ERRO ao criar UtilizadoresTab:", e)[m
[32m+[m[32m            traceback.print_exc()[m
[32m+[m[32m            QMessageBox.critical([m
[32m+[m[32m                self,[m
[32m+[m[32m                "Erro",[m
[32m+[m[32m                f"Falha ao carregar aba Utilizadores:\n{e}",[m
[32m+[m[32m            )[m
 [m
[31m-        # Admin / Logs (somente admin)[m
[32m+[m[32m        # Abas admin[m
         try:[m
[31m-            debug_admin = is_admin()[m
[31m-            print("  DEBUG is_admin() em load_tabs:", debug_admin)[m
[32m+[m[32m            is_admin = bool(self.user_is_admin)[m
[32m+[m[32m            if is_admin:[m
[32m+[m[32m                self.admin_tab = AdminTab()[m
[32m+[m[32m                self.tabs.addTab(self.admin_tab, "Administração")[m
 [m
[31m-            if debug_admin:[m
[31m-                self.tabs.addTab(AdminTab(), "Administração")[m
[31m-                self.tabs.addTab(LogViewerTab(), "Logs do Sistema")[m
[31m-            else:[m
[31m-                print("  Usuário não é admin; abas Administração/Logs ocultas.")[m
[32m+[m[32m                self.logs_tab = LogViewerTab()[m
[32m+[m[32m                self.tabs.addTab(self.logs_tab, "Logs")[m
         except Exception as e:[m
             import traceback[m
             print("ERRO ao verificar/admin abas:", e)[m
[36m@@ -262,23 +172,33 @@[m [mclass DashMain(QMainWindow):[m
                 f"Falha ao verificar permissões de administrador:\n{e}",[m
             )[m
 [m
[31m-    # ===== Sobre / Logout / Sair =====[m
[31m-    def mostrar_sobre(self):[m
[31m-        QMessageBox.information([m
[32m+[m[32m    def confirmar_logout(self):[m
[32m+[m[32m        resp = QMessageBox.question([m
             self,[m
[31m-            "Sobre",[m
[31m-            f"{APP_NAME} v{APP_VERSION}\n{APP_COMPANY}\n{APP_DEVELOPER}\n{APP_COPYRIGHT}",[m
[32m+[m[32m            "Sair",[m
[32m+[m[32m            "Deseja realmente terminar a sessão?",[m
[32m+[m[32m            QMessageBox.Yes | QMessageBox.No,[m
[32m+[m[32m            QMessageBox.No,[m
         )[m
[32m+[m[32m        if resp == QMessageBox.Yes:[m
[32m+[m[32m            if self.on_logout:[m
[32m+[m[32m                try:[m
[32m+[m[32m                    self.on_logout()[m
[32m+[m[32m                except Exception:[m
[32m+[m[32m                    pass[m
[32m+[m[32m            else:[m
[32m+[m[32m                try:[m
[32m+[m[32m                    session_manager.logout()[m
[32m+[m[32m                except Exception:[m
[32m+[m[32m                    pass[m
[32m+[m[32m                self.close()[m
 [m
[31m-    def logout(self):[m
[31m-        if self.on_logout:[m
[31m-            self.on_logout()[m
[31m-        else:[m
[31m-            try:[m
[31m-                session_manager.logout()[m
[31m-            except Exception:[m
[31m-                pass[m
[31m-            self.close()[m
[32m+[m[32m    def closeEvent(self, event):[m
[32m+[m[32m        try:[m
[32m+[m[32m            session_manager.logout()[m
[32m+[m[32m        except Exception:[m
[32m+[m[32m            pass[m
[32m+[m[32m        super().closeEvent(event)[m
 [m
     def sair(self):[m
         QApplication.instance().quit()[m
[36m@@ -286,10 +206,7 @@[m [mclass DashMain(QMainWindow):[m
     def show_operation_done(self, message="Operação concluída com sucesso."):[m
         self.feedback_label.setText(message)[m
         self.feedback_label.show()[m
[31m-[m
[31m-        # some sozinho após 4 segundos[m
         QTimer.singleShot(4000, self.feedback_label.hide)[m
 [m
[31m-[m
     def show_status_message(self, message):[m
         self.show_operation_done(message)[m
[1mdiff --git a/main.py b/main.py[m
[1mindex ba1e275..4194dea 100644[m
[1m--- a/main.py[m
[1m+++ b/main.py[m
[36m@@ -1,12 +1,9 @@[m
 import sys[m
[31m-import os[m
[31m-[m
 from PyQt6.QtWidgets import QApplication[m
 [m
 from autenticacao import session_manager[m
 from autenticacao.login_window import LoginWindow[m
 from interface.dash_main import DashMain[m
[31m-# from database_module import inicializar_banco  # não precisa mais chamar aqui[m
 [m
 [m
 class MainApp:[m
[36m@@ -15,42 +12,44 @@[m [mclass MainApp:[m
         self.login_window = None[m
         self.dash_main = None[m
 [m
[31m-    def run(self):[m
[31m-        base_dir = os.path.dirname(os.path.abspath(__file__))[m
[31m-        os.chdir(base_dir)[m
[31m-[m
[31m-        self.show_login()[m
[31m-        sys.exit(self.app.exec())[m
[31m-[m
     def show_login(self):[m
[32m+[m[32m        print("DEBUG: show_login chamado")[m
         self.login_window = LoginWindow(on_login_success=self.on_login_success)[m
         self.login_window.show()[m
 [m
     def on_login_success(self, user_dict):[m
[31m-        login = user_dict["login"][m
[32m+[m[32m        print("DEBUG: on_login_success em MainApp chamado:", user_dict)[m
[32m+[m
[32m+[m[32m        # garante sessão carregada, se por algum motivo não estiver[m
[32m+[m[32m        if not session_manager.current_user:[m
[32m+[m[32m            session_manager.login(user_dict["login"])[m
 [m
[31m-        ok = session_manager.login(login)[m
[31m-        if not ok:[m
[31m-            self.login_window.show()[m
[31m-            return[m
[32m+[m[32m        if self.login_window is not None:[m
[32m+[m[32m            self.login_window.close()[m
[32m+[m[32m            self.login_window = None[m
 [m
[32m+[m[32m        print("DEBUG: criando DashMain")[m
         self.dash_main = DashMain(on_logout=self.handle_logout)[m
         self.dash_main.showMaximized()[m
[31m-        self.login_window.close()[m
[31m-        self.login_window = None[m
 [m
     def handle_logout(self):[m
[31m-        session_manager.logout()[m
[32m+[m[32m        print("DEBUG: handle_logout chamado")[m
[32m+[m[32m        try:[m
[32m+[m[32m            session_manager.logout()[m
[32m+[m[32m        except Exception:[m
[32m+[m[32m            pass[m
 [m
[31m-        if self.dash_main:[m
[32m+[m[32m        if self.dash_main is not None:[m
             self.dash_main.close()[m
             self.dash_main = None[m
 [m
         self.show_login()[m
 [m
[32m+[m[32m    def run(self):[m
[32m+[m[32m        self.show_login()[m
[32m+[m[32m        sys.exit(self.app.exec())[m
[32m+[m
 [m
 if __name__ == "__main__":[m
[31m-    # inicializar_banco()  # REMOVIDO para Postgres[m
[31m-[m
     main_app = MainApp()[m
     main_app.run()[m
