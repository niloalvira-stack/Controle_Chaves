# admin/utilizadores_tab.py
import csv
import logging
from contextlib import closing

from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QFileDialog, QDialog, QFormLayout, QLineEdit,
    QComboBox, QHeaderView, QDateEdit
)

from email_validator import validate_email, EmailNotValidError

from autenticacao import get_current_user, validar_login, is_admin
from utils.utils_log import log_acao
from database_module import get_connection, execute_query

logger = logging.getLogger(__name__)


class UtilizadorDialog(QDialog):
    def __init__(self, parent=None, dados=None):
        super().__init__(parent)
        self.dados = dados or {}
        self._setup_ui()
        self._carregar_dados()

    def _setup_ui(self):
        self.setWindowTitle("Utilizador")
        layout = QFormLayout(self)

        self.edit_nome = QLineEdit()
        self.edit_email = QLineEdit()

        self.combo_vinculo = QComboBox()
        self.combo_vinculo.addItems([
            "Servidor(a)",
            "Aluno(a)",
            "Bolsista",
            "Monitor(a)",
            "Estagiário(a)",
            "Externo(a)",
        ])

        self.combo_ativo = QComboBox()
        self.combo_ativo.addItems(["Sim", "Não"])

        self.date_fim = QDateEdit()
        self.date_fim.setCalendarPopup(True)
        self.date_fim.setDisplayFormat("dd/MM/yyyy")
        self.date_fim.setDate(QDate.currentDate())

        layout.addRow("Nome:", self.edit_nome)
        layout.addRow("E-mail:", self.edit_email)
        layout.addRow("Vínculo:", self.combo_vinculo)
        layout.addRow("Ativo:", self.combo_ativo)
        layout.addRow("Válido até:", self.date_fim)

        btn_box = QHBoxLayout()
        self.btn_salvar = QPushButton("Salvar")
        self.btn_cancelar = QPushButton("Cancelar")
        btn_box.addWidget(self.btn_salvar)
        btn_box.addWidget(self.btn_cancelar)
        layout.addRow(btn_box)

        self.btn_salvar.clicked.connect(self.accept)
        self.btn_cancelar.clicked.connect(self.reject)

    def _carregar_dados(self):
        if not self.dados:
            return

        self.edit_nome.setText(self.dados.get("nome", ""))
        self.edit_email.setText(self.dados.get("email", ""))

        vinculo = self.dados.get("vinculo", "")
        idx = self.combo_vinculo.findText(vinculo)
        if idx >= 0:
            self.combo_vinculo.setCurrentIndex(idx)

        self.combo_ativo.setCurrentIndex(0 if self.dados.get("ativo", True) else 1)

        data_fim = self.dados.get("data_fim_validade")
        if data_fim:
            if isinstance(data_fim, str):
                try:
                    ano, mes, dia = map(int, data_fim.split("-"))
                    qd = QDate(ano, mes, dia)
                except Exception:
                    qd = QDate.currentDate()
            else:
                qd = QDate(data_fim.year, data_fim.month, data_fim.day)
            self.date_fim.setDate(qd)
        else:
            self.date_fim.setDate(QDate.currentDate())

    def get_dados(self):
        nome = self.edit_nome.text().strip()
        email = self.edit_email.text().strip()
        vinculo = self.combo_vinculo.currentText()
        ativo = self.combo_ativo.currentText() == "Sim"
        data_fim = self.date_fim.date().toPyDate()

        if vinculo == "Servidor(a)":
            data_fim = None

        return {
            "nome": nome,
            "email": email,
            "vinculo": vinculo,
            "ativo": ativo,
            "data_fim_validade": data_fim,
        }


class UtilizadoresTab(QWidget):
    def __init__(self, movimentacoes_tab=None, parent=None):
        super().__init__(parent)
        self.icon_ativo = QIcon("icons/ok.png")
        self.icon_inativo = QIcon("icons/x.png")

        self.movimentacoes_tab = movimentacoes_tab
        self._setup_ui()
        self.carregar_dados()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nome", "E-mail", "Vínculo", "Ativo", "Válido até"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        btn_layout = QHBoxLayout()
        self.btn_novo = QPushButton("Novo")
        self.btn_editar = QPushButton("Editar")
        self.btn_excluir = QPushButton("Excluir")
        self.btn_ativar = QPushButton("Ativar/Desativar")
        self.btn_exportar = QPushButton("Exportar CSV")

        btn_layout.addWidget(self.btn_novo)
        btn_layout.addWidget(self.btn_editar)
        btn_layout.addWidget(self.btn_excluir)
        btn_layout.addWidget(self.btn_ativar)
        btn_layout.addWidget(self.btn_exportar)

        layout.addWidget(self.table)
        layout.addLayout(btn_layout)

        self.btn_novo.clicked.connect(self.novo_utilizador)
        self.btn_editar.clicked.connect(self.editar_utilizador)
        self.btn_excluir.clicked.connect(self.excluir_utilizador)
        self.btn_ativar.clicked.connect(self.ativar_desativar_utilizador)
        self.btn_exportar.clicked.connect(self.exportar_csv)

    def _email_valido_completo(self, email: str):
        email = (email or "").strip()

        if not email:
            QMessageBox.warning(
                self,
                "Dados incompletos",
                "E-mail é obrigatório.",
            )
            return False, ""

        try:
            info = validate_email(email, check_deliverability=False)
            email_norm = info.normalized
        except EmailNotValidError as e:
            QMessageBox.warning(
                self,
                "Endereço de e-mail inválido",
                f"Endereço de e-mail inválido: {str(e)}",
            )
            return False, email

        try:
            dominio = email_norm.split("@", 1)[1]
        except IndexError:
            QMessageBox.warning(
                self,
                "Endereço de e-mail inválido",
                "O e-mail informado não contém um domínio válido.",
            )
            return False, email_norm

        partes = dominio.rsplit(".", 1)
        if len(partes) == 2 and len(partes[1]) < 2:
            QMessageBox.warning(
                self,
                "Endereço de e-mail inválido",
                "O domínio do e-mail deve ter um TLD com pelo menos 2 letras.",
            )
            return False, email_norm

        return True, email_norm.lower()

    def carregar_dados(self):
        self.table.setRowCount(0)
        try:
            conn = get_connection()
            if conn is None:
                QMessageBox.critical(
                    self,
                    "Erro",
                    "Não foi possível conectar ao banco de dados.",
                )
                return

            with closing(conn), conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, nome, email, vinculo, ativo, data_fim_validade
                    FROM utilizadores
                    ORDER BY id
                    """
                )
                rows = cur.fetchall()

            for row in rows:
                self._adicionar_linha(row)

        except Exception as e:
            logger.error(f"Erro ao carregar utilizadores: {e}")
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao carregar utilizadores: {e}",
            )

    def _adicionar_linha(self, row):
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)

        if hasattr(row, "keys"):
            id_ = row.get("id")
            nome = row.get("nome", "")
            email = row.get("email", "")
            vinculo = row.get("vinculo", "")
            ativo = row.get("ativo", False)
            data_fim = row.get("data_fim_validade")
        else:
            id_, nome, email, vinculo, ativo, data_fim = row

        if isinstance(nome, (bytes, bytearray)):
            nome = nome.decode("utf-8")
        if isinstance(email, (bytes, bytearray)):
            email = email.decode("utf-8")
        if isinstance(vinculo, (bytes, bytearray)):
            vinculo = vinculo.decode("utf-8")

        id_item = QTableWidgetItem("" if id_ is None else str(id_))
        nome_item = QTableWidgetItem(str(nome or ""))
        email_item = QTableWidgetItem(str(email or ""))
        vinculo_item = QTableWidgetItem(str(vinculo or ""))

        ativo_bool = bool(ativo)
        status_texto = "Sim" if ativo_bool else "Não"
        status_item = QTableWidgetItem(status_texto)
        status_item.setData(Qt.ItemDataRole.UserRole, ativo_bool)

        if not self.icon_ativo.isNull() and not self.icon_inativo.isNull():
            status_item.setIcon(self.icon_ativo if ativo_bool else self.icon_inativo)

        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        if data_fim:
            try:
                texto_data = data_fim.strftime("%d/%m/%Y")
            except Exception:
                texto_data = str(data_fim)
        else:
            texto_data = ""

        data_item = QTableWidgetItem(texto_data)
        data_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        itens = [id_item, nome_item, email_item, vinculo_item, status_item, data_item]

        for col, item in enumerate(itens):
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, col, item)

    def _get_linha_selecionada(self):
        linhas = self.table.selectionModel().selectedRows()
        if not linhas:
            QMessageBox.information(
                self,
                "Seleção necessária",
                "Selecione um utilizador na tabela.",
            )
            return None
        return linhas[0].row()

    def _get_dados_linha(self, row_idx):
        ativo_item = self.table.item(row_idx, 4)
        ativo_val = ativo_item.data(Qt.ItemDataRole.UserRole)
        if ativo_val is None:
            texto = (ativo_item.text() or "").strip().lower()
            ativo_val = texto in ("sim", "ativo", "true", "1")

        data_item = self.table.item(row_idx, 5)
        data_fim = data_item.text().strip() if data_item and data_item.text() else None

        return {
            "id": int(self.table.item(row_idx, 0).text()),
            "nome": self.table.item(row_idx, 1).text(),
            "email": self.table.item(row_idx, 2).text(),
            "vinculo": self.table.item(row_idx, 3).text(),
            "ativo": bool(ativo_val),
            "data_fim_validade": data_fim,
        }

    def novo_utilizador(self):
        dlg = UtilizadorDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dados = dlg.get_dados()

            ok_email, email_normalizado = self._email_valido_completo(dados["email"])
            if not ok_email:
                return
            dados["email"] = email_normalizado

            if not dados["nome"]:
                QMessageBox.warning(
                    self,
                    "Dados incompletos",
                    "Nome é obrigatório.",
                )
                return

            try:
                with closing(get_connection()) as conn, conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO utilizadores (nome, email, vinculo, ativo, data_fim_validade)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            dados["nome"],
                            dados["email"] or None,
                            dados["vinculo"] or None,
                            dados["ativo"],
                            dados["data_fim_validade"],
                        ),
                    )

                    ret = cur.fetchone()
                    novo_id = ret.get("id") if hasattr(ret, "keys") else ret[0]
                    conn.commit()

                user = get_current_user()
                user_login = user.get("login", "") if isinstance(user, dict) else str(user or "")

                log_acao(
                    "create_user",
                    user=user_login,
                    resource=f"utilizador:{novo_id}",
                    status="success",
                    details=f"Cadastrou utilizador ID {novo_id}",
                )
                self.carregar_dados()
                self._atualizar_combo_movimentacoes()

            except Exception as e:
                logger.error(f"Erro ao criar utilizador: {e}")
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Erro ao criar utilizador: {e}",
                )

    def editar_utilizador(self):
        row_idx = self._get_linha_selecionada()
        if row_idx is None:
            return

        dados_orig = self._get_dados_linha(row_idx)
        dlg = UtilizadorDialog(self, dados=dados_orig)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            dados = dlg.get_dados()

            ok_email, email_normalizado = self._email_valido_completo(dados["email"])
            if not ok_email:
                return
            dados["email"] = email_normalizado

            if not dados["nome"]:
                QMessageBox.warning(
                    self,
                    "Dados incompletos",
                    "Nome é obrigatório.",
                )
                return

            try:
                with closing(get_connection()) as conn, conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE utilizadores
                        SET nome = %s,
                            email = %s,
                            vinculo = %s,
                            ativo = %s,
                            data_fim_validade = %s
                        WHERE id = %s
                        """,
                        (
                            dados["nome"],
                            dados["email"] or None,
                            dados["vinculo"] or None,
                            dados["ativo"],
                            dados["data_fim_validade"],
                            dados_orig["id"],
                        ),
                    )
                    conn.commit()

                user = get_current_user()
                user_login = user.get("login", "") if isinstance(user, dict) else str(user or "")

                log_acao(
                    "update_user",
                    user=user_login,
                    resource=f"utilizador:{dados_orig['id']}",
                    status="success",
                    details=f"Editou utilizador ID {dados_orig['id']}",
                )

                self.carregar_dados()
                self._atualizar_combo_movimentacoes()

            except Exception as e:
                logger.error(f"Erro ao editar utilizador: {e}")
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Erro ao editar utilizador: {e}",
                )

    def excluir_utilizador(self):
        if not is_admin():
            QMessageBox.warning(
                self,
                "Permissão negada",
                "Apenas administradores podem excluir utilizadores.",
            )
            return

        row_idx = self._get_linha_selecionada()
        if row_idx is None:
            return

        dados = self._get_dados_linha(row_idx)

        user_dict = get_current_user() or {}
        login_atual = user_dict.get("login", "") if isinstance(user_dict, dict) else str(user_dict)

        ok = validar_login(login_atual)
        if not ok:
            QMessageBox.warning(
                self,
                "Sessão inválida",
                "Não foi possível validar o usuário atual. Faça login novamente.",
            )
            return

        resp = QMessageBox.question(
            self,
            "Confirmação",
            (
                f"Tem certeza que deseja excluir o utilizador '{dados['nome']}'?\n"
                f"Esta ação não poderá ser desfeita."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        try:
            with closing(get_connection()) as conn, conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM utilizadores WHERE id = %s",
                    (dados["id"],),
                )
                conn.commit()

            log_acao(
                "delete_user",
                user=login_atual,
                resource=f"utilizador:{dados['id']}",
                status="success",
                details=f"Excluiu utilizador ID {dados['id']} ({dados['nome']})",
            )
            self.carregar_dados()
            self._atualizar_combo_movimentacoes()

        except Exception as e:
            logger.error(f"Erro ao excluir utilizador: {e}")
            QMessageBox.warning(
                self,
                "Não permitido",
                "Este utilizador pode possuir movimentações associadas.\n"
                "Use apenas 'Ativar/Desativar'.",
            )

    def ativar_desativar_utilizador(self):
        row_idx = self._get_linha_selecionada()
        if row_idx is None:
            return

        dados = self._get_dados_linha(row_idx)
        novo_status = not dados["ativo"]

        try:
            with closing(get_connection()) as conn, conn.cursor() as cur:
                cur.execute(
                    "UPDATE utilizadores SET ativo = %s WHERE id = %s",
                    (novo_status, dados["id"]),
                )
                conn.commit()

            user = get_current_user()
            user_login = user.get("login", "") if isinstance(user, dict) else str(user or "")

            log_acao(
                "toggle_user",
                user=user_login,
                resource=f"utilizador:{dados['id']}",
                status="success",
                details="Ativou utilizador" if novo_status else "Desativou utilizador",
            )
            self.carregar_dados()
            self._atualizar_combo_movimentacoes()

        except Exception as e:
            logger.error(f"Erro ao alterar status do utilizador: {e}")
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao alterar status do utilizador: {e}",
            )

    def exportar_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar utilizadores como CSV",
            "",
            "CSV Files (*.csv)",
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["ID", "Nome", "E-mail", "Vínculo", "Ativo", "Válido até"])

                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)

            QMessageBox.information(
                self,
                "Exportação concluída",
                "Utilizadores exportados com sucesso.",
            )

        except Exception as e:
            logger.error(f"Erro no export CSV: {e}")
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao exportar: {e}",
            )

    def _atualizar_combo_movimentacoes(self):
        if self.movimentacoes_tab:
            try:
                self.movimentacoes_tab.load_utilizadores_combo()
            except Exception as e:
                logger.warning(f"Falha ao atualizar combo: {e}")