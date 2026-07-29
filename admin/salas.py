from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QMessageBox, QFileDialog, QHeaderView,
    QLabel, QDialogButtonBox, QComboBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from utils.button_style import aplicar_estilo_botao_padrao

import csv

from database_module import get_connection

print("DEBUG: carregando admin/salas.py - classe SalasTab nova")


class SalaDialog(QDialog):
    # ✅ Adicionei o parametro tipo_chave e o combo novo
    def __init__(self, predios, anexos, nome="", descricao="", predio_id=None, anexo_id=None, tipo_chave="principal", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastro/Editar Sala")

        layout = QFormLayout(self)

        self.nome_edit = QLineEdit(nome)
        self.descricao_edit = QLineEdit(descricao)

        self.combo_predio = QComboBox()
        self.combo_predio.addItem("Nenhum", None)
        for row in predios:
            if isinstance(row, dict):
                pid = row.get("id")
                pname = row.get("nome")
            else:
                pid, pname = row

            if isinstance(pname, (bytes, bytearray)):
                pname = pname.decode("utf-8")

            self.combo_predio.addItem(str(pname or ""), pid)

        if predio_id is not None:
            idx = self.combo_predio.findData(predio_id)
            if idx >= 0:
                self.combo_predio.setCurrentIndex(idx)

        self.combo_anexo = QComboBox()
        self.combo_anexo.addItem("Nenhum", None)
        for row in anexos:
            if isinstance(row, dict):
                aid = row.get("id")
                aname = row.get("nome")
            else:
                aid, aname = row

            if isinstance(aname, (bytes, bytearray)):
                aname = aname.decode("utf-8")

            self.combo_anexo.addItem(str(aname or ""), aid)

        if anexo_id is not None:
            idx = self.combo_anexo.findData(anexo_id)
            if idx >= 0:
                self.combo_anexo.setCurrentIndex(idx)

        # ✅ CAMPO NOVO: TIPO DA CHAVE
        self.combo_tipo_chave = QComboBox()
        self.combo_tipo_chave.addItem("Chave Principal", "principal")
        self.combo_tipo_chave.addItem("Cópia / Reserva", "reserva")
        # Seleciona o valor atual
        idx_tipo = self.combo_tipo_chave.findData(tipo_chave)
        if idx_tipo >= 0:
            self.combo_tipo_chave.setCurrentIndex(idx_tipo)

        layout.addRow("Nome da sala:", self.nome_edit)
        layout.addRow("Descrição:", self.descricao_edit)
        layout.addRow("Prédio:", self.combo_predio)
        layout.addRow("Anexo:", self.combo_anexo)
        layout.addRow("Tipo de Chave Vinculada:", self.combo_tipo_chave) # ✅ Adicionado

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {
            "nome": self.nome_edit.text().strip(),
            "descricao": self.descricao_edit.text().strip(),
            "predio_id": self.combo_predio.currentData(),
            "anexo_id": self.combo_anexo.currentData(),
            "tipo_chave": self.combo_tipo_chave.currentData(), # ✅ Retorna o tipo escolhido
        }


class SalasTab(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        print("DEBUG: SalasTab.__init__ (nova) chamada")
        self.setWindowTitle("Gestão de Salas")

        self.init_ui()
        self.load_salas()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(15)

        label = QLabel("Gestão de Salas")
        layout_principal.addWidget(label)

        layout_botoes = QHBoxLayout()
        layout_botoes.setSpacing(12)
        layout_botoes.setContentsMargins(0, 0, 0, 15)

        self.btn_add = QPushButton("Cadastrar Sala")
        self.btn_edit = QPushButton("Editar Sala")
        self.btn_delete = QPushButton("Excluir Sala")
        self.btn_exportar = QPushButton("Exportar CSV")
        self.btn_exportar_pdf = QPushButton("Exportar PDF")

        aplicar_estilo_botao_padrao(self.btn_add, "#0d6efd", "#ffffff")
        aplicar_estilo_botao_padrao(self.btn_edit, "#fd7e14", "#ffffff")
        aplicar_estilo_botao_padrao(self.btn_delete, "#dc3545", "#ffffff")
        aplicar_estilo_botao_padrao(self.btn_exportar, "#198754", "#ffffff")
        aplicar_estilo_botao_padrao(self.btn_exportar_pdf, "#6c757d", "#ffffff")

        self.definir_icone(self.btn_add, "recursos/icones/adicionar.png")
        self.definir_icone(self.btn_edit, "recursos/icones/editar.png")
        self.definir_icone(self.btn_delete, "recursos/icones/excluir.png")
        self.definir_icone(self.btn_exportar, "recursos/icones/csv.png")
        self.definir_icone(self.btn_exportar_pdf, "recursos/icones/pdf.png")

        layout_botoes.addWidget(self.btn_add)
        layout_botoes.addWidget(self.btn_edit)
        layout_botoes.addWidget(self.btn_delete)
        layout_botoes.addStretch()
        layout_botoes.addWidget(self.btn_exportar)
        layout_botoes.addWidget(self.btn_exportar_pdf)

        layout_principal.addLayout(layout_botoes)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Descrição", "Prédio", "Anexo", "Status"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setColumnHidden(0, True)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)

        layout_principal.addWidget(self.table)

        self.btn_add.clicked.connect(self.adicionar_sala)
        self.btn_edit.clicked.connect(self.editar_sala)
        self.btn_delete.clicked.connect(self.excluir_sala)
        self.btn_exportar.clicked.connect(self.exportar_csv)
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)

    def definir_icone(self, botao, caminho):
        icone = QIcon(caminho)
        if not icone.isNull():
            botao.setIcon(icone)
            botao.setIconSize(QSize(16, 16))

    def _get_dash_main(self):
        janela = self.parentWidget()
        while janela is not None and janela.__class__.__name__ != "DashMain":
            janela = janela.parentWidget()
        return janela

    def _show_success(self, mensagem):
        dash = self._get_dash_main()
        if dash:
            dash.show_operation_done(mensagem)

    def _decode_if_bytes(self, valor):
        if isinstance(valor, (bytes, bytearray)):
            return valor.decode("utf-8")
        return valor

    def _row_get(self, row, key_or_index, default=None):
        if isinstance(row, dict):
            return row.get(key_or_index, default)
        try:
            return row[key_or_index]
        except (IndexError, KeyError, TypeError):
            return default

    def _obter_sala_id_da_linha(self, row):
        nome_item = self.table.item(row, 1)
        if nome_item:
            sala_id = nome_item.data(Qt.ItemDataRole.UserRole)
            if sala_id is not None:
                return sala_id

        id_item = self.table.item(row, 0)
        if id_item:
            texto = id_item.text().strip()
            if texto.isdigit():
                return int(texto)

        return None
    def fetch_predios(self):
        conn = None
        try:
            conn = get_connection()
            if conn is None:
                return []

            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM predios ORDER BY nome")
            return cursor.fetchall()
        except Exception:
            return []
        finally:
            if conn:
                conn.close()

    def fetch_anexos(self):
        conn = None
        try:
            conn = get_connection()
            if conn is None:
                return []

            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM anexos ORDER BY nome")
            return cursor.fetchall()
        except Exception:
            return []
        finally:
            if conn:
                conn.close()

    def load_salas(self):
        self.table.setRowCount(0)
        conn = None
        try:
            conn = get_connection()
            if conn is None:
                return

            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id,
                       s.nome,
                       s.descricao,
                       p.nome AS predio_nome,
                       a.nome AS anexo_nome,
                       s.status
                FROM salas s
                LEFT JOIN predios p ON s.predio_id = p.id
                LEFT JOIN anexos a ON s.anexo_id = a.id
                ORDER BY s.nome
            """)
            salas = cursor.fetchall()
            print("DEBUG salas em SalasTab:", salas)

            for row_idx, row in enumerate(salas):
                if isinstance(row, dict):
                    sid = row.get("id")
                    nome = row.get("nome")
                    descricao = row.get("descricao")
                    predio_nome = row.get("predio_nome")
                    anexo_nome = row.get("anexo_nome")
                    status = row.get("status")
                else:
                    sid = self._row_get(row, 0)
                    nome = self._row_get(row, 1)
                    descricao = self._row_get(row, 2)
                    predio_nome = self._row_get(row, 3)
                    anexo_nome = self._row_get(row, 4)
                    status = self._row_get(row, 5)

                nome = self._decode_if_bytes(nome)
                descricao = self._decode_if_bytes(descricao)
                predio_nome = self._decode_if_bytes(predio_nome)
                anexo_nome = self._decode_if_bytes(anexo_nome)
                status = self._decode_if_bytes(status)

                self.table.insertRow(row_idx)

                item_id = QTableWidgetItem(str(sid) if sid is not None else "")
                item_nome = QTableWidgetItem(nome or "")
                item_desc = QTableWidgetItem(descricao or "")
                item_predio = QTableWidgetItem(predio_nome or "")
                item_anexo = QTableWidgetItem(anexo_nome or "")
                item_status = QTableWidgetItem(status or "")

                item_nome.setData(Qt.ItemDataRole.UserRole, sid)

                self.table.setItem(row_idx, 0, item_id)
                self.table.setItem(row_idx, 1, item_nome)
                self.table.setItem(row_idx, 2, item_desc)
                self.table.setItem(row_idx, 3, item_predio)
                self.table.setItem(row_idx, 4, item_anexo)
                self.table.setItem(row_idx, 5, item_status)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar salas: {e}")
        finally:
            if conn:
                conn.close()

    def _validar_nome_sala(self, nome):
        return bool(nome.strip())

    def adicionar_sala(self):
        predios = self.fetch_predios()
        anexos = self.fetch_anexos()

        dialog = SalaDialog(predios, anexos, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            nome = data["nome"]
            tipo_chave = data["tipo_chave"]

            if not self._validar_nome_sala(nome):
                QMessageBox.warning(self, "Atenção", "Nome da sala é obrigatório.")
                return

            conn = None
            try:
                conn = get_connection()
                if conn is None:
                    return

                cursor = conn.cursor()
                # 1. INSERE A SALA
                cursor.execute(
                    """
                    INSERT INTO salas (nome, descricao, predio_id, anexo_id, status)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (nome, data["descricao"], data["predio_id"], data["anexo_id"], "disponivel"),
                )
                res = cursor.fetchone()
                if not res:
                    raise Exception("Não foi possível obter o ID da sala.")

                sala_id = res[0] if isinstance(res, (list, tuple)) else res.get("id")

                # ✅ CORREÇÃO: CRIA A CHAVE FÍSICA AUTOMATICAMENTE!
                etiqueta = f"{nome} - {data['descricao']}" if data["descricao"] else nome
                cursor.execute(
                    """
                    INSERT INTO chaves_fisicas (sala_id, etiqueta, tipo, status, ativa)
                    VALUES (%s, %s, %s, 'disponivel', TRUE)
                    """,
                    (sala_id, etiqueta, tipo_chave)
                )

                conn.commit()
                self.load_salas()
                self._show_success("Sala e chave cadastradas com sucesso!")

            except Exception as e:
                if conn:
                    conn.rollback()
                QMessageBox.critical(self, "Erro", f"Falha: {repr(e)}")

            finally:
                if conn:
                    conn.close()

    def editar_sala(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma sala para editar.")
            return

        sala_id = self._obter_sala_id_da_linha(row)
        if sala_id is None:
            QMessageBox.warning(self, "Erro", "ID da sala não encontrado.")
            return

        nome_item = self.table.item(row, 1)
        desc_item = self.table.item(row, 2)
        predio_item = self.table.item(row, 3)
        anexo_item = self.table.item(row, 4)

        nome_atual = nome_item.text() if nome_item else ""
        descricao_atual = desc_item.text() if desc_item else ""
        predio_nome_atual = predio_item.text() if predio_item else ""
        anexo_nome_atual = anexo_item.text() if anexo_item else ""

        predios = self.fetch_predios()
        anexos = self.fetch_anexos()

        predio_id_atual = None
        for row_predio in predios:
            if isinstance(row_predio, dict):
                pid = row_predio.get("id")
                pname = row_predio.get("nome")
            else:
                pid, pname = row_predio

            pname = self._decode_if_bytes(pname)
            if pname == predio_nome_atual:
                predio_id_atual = pid
                break

        anexo_id_atual = None
        for row_anexo in anexos:
            if isinstance(row_anexo, dict):
                aid = row_anexo.get("id")
                aname = row_anexo.get("nome")
            else:
                aid, aname = row_anexo

            aname = self._decode_if_bytes(aname)
            if aname == anexo_nome_atual:
                anexo_id_atual = aid
                break

        # ✅ BUSCA O TIPO ATUAL DA CHAVE PARA PREENCHER O FORMULÁRIO
        tipo_atual = "principal"
        conn_tmp = get_connection()
        try:
            cur_tmp = conn_tmp.cursor()
            cur_tmp.execute("SELECT tipo FROM chaves_fisicas WHERE sala_id = %s AND ativa = TRUE LIMIT 1", (sala_id,))
            res = cur_tmp.fetchone()
            if res:
                # ✅ Funciona com tupla OU dicionário
                tipo_atual = res[0] if isinstance(res, (list, tuple)) else res.get("tipo", "principal")
        finally:
            conn_tmp.close()

        dialog = SalaDialog(
            predios,
            anexos,
            nome=nome_atual,
            descricao=descricao_atual,
            predio_id=predio_id_atual,
            anexo_id=anexo_id_atual,
            tipo_chave=tipo_atual,
            parent=self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            nome_novo = data["nome"]
            tipo_chave = data["tipo_chave"]

            if not self._validar_nome_sala(nome_novo):
                QMessageBox.warning(self, "Atenção", "Nome da sala é obrigatório.")
                return

            conn = None
            try:
                conn = get_connection()
                if conn is None:
                    return

                cursor = conn.cursor()
                # 1. Atualiza dados da sala
                cursor.execute(
                    """
                    UPDATE salas
                    SET nome = %s, descricao = %s, predio_id = %s, anexo_id = %s
                    WHERE id = %s
                    """,
                    (nome_novo, data["descricao"], data["predio_id"], data["anexo_id"], sala_id),
                )
                # ✅ 2. ATUALIZA O TIPO NA CHAVE FÍSICA
                cursor.execute(
                    """
                    UPDATE chaves_fisicas
                    SET tipo = %s, atualizada_em = CURRENT_TIMESTAMP
                    WHERE sala_id = %s AND ativa = TRUE
                    """,
                    (tipo_chave, sala_id)
                )

                conn.commit()
                self.load_salas()
                self._show_success("Sala e tipo de chave atualizados com sucesso!")
            except Exception as e:
                if conn:
                    conn.rollback()
                QMessageBox.critical(self, "Erro", f"Erro ao editar sala: {e}")
            finally:
                if conn:
                    conn.close()


    def excluir_sala(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma sala para excluir.")
            return

        sala_id = self._obter_sala_id_da_linha(row)
        nome_item = self.table.item(row, 1)

        if sala_id is None or not nome_item:
            QMessageBox.warning(self, "Erro", "Registro inválido.")
            return

        nome = nome_item.text()

        resp = QMessageBox.question(
            self,
            "Confirmação",
            f"Tem certeza que deseja excluir a sala '{nome}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if resp == QMessageBox.StandardButton.Yes:
            conn = None
            try:
                conn = get_connection()
                if conn is None:
                    return

                cursor = conn.cursor()
                cursor.execute("DELETE FROM salas WHERE id = %s", (sala_id,))
                conn.commit()
                self.load_salas()
                self._show_success("Sala excluída com sucesso!")
            except Exception as e:
                if conn:
                    conn.rollback()
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Erro ao excluir sala: {e}"
                )
            finally:
                if conn:
                    conn.close()

    def exportar_csv(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar salas para CSV", "salas.csv", "CSV (*.csv)"
        )
        if not filename:
            return

        try:
            colunas_visiveis = [
                col for col in range(self.table.columnCount())
                if not self.table.isColumnHidden(col)
            ]

            headers = [
                self.table.horizontalHeaderItem(col).text()
                for col in colunas_visiveis
            ]

            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)

                for row in range(self.table.rowCount()):
                    rowdata = []
                    for col in colunas_visiveis:
                        item = self.table.item(row, col)
                        rowdata.append(item.text() if item else "")
                    writer.writerow(rowdata)

            self._show_success("Salas exportadas para CSV com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV: {e}")

    def exportar_pdf(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar salas para PDF", "salas.pdf", "PDF (*.pdf)"
        )
        if not filename:
            return

        try:
            styles = getSampleStyleSheet()
            estilo = styles["BodyText"]
            estilo.fontName = "Helvetica"
            estilo.fontSize = 8
            estilo.leading = 10

            colunas_visiveis = [
                col for col in range(self.table.columnCount())
                if not self.table.isColumnHidden(col)
            ]

            headers = [
                Paragraph(self.table.horizontalHeaderItem(col).text(), styles["Heading5"])
                for col in colunas_visiveis
            ]

            data = [headers]

            for row in range(self.table.rowCount()):
                rowdata = []
                for col in colunas_visiveis:
                    item = self.table.item(row, col)
                    texto = item.text() if item else ""
                    rowdata.append(Paragraph(texto.replace("\n", "<br/>"), estilo))
                data.append(rowdata)

            doc = SimpleDocTemplate(filename, pagesize=A4)

            largura_util = A4[0] - doc.leftMargin - doc.rightMargin
            qtd_cols = len(colunas_visiveis)
            col_width = largura_util / qtd_cols if qtd_cols else largura_util
            col_widths = [col_width] * qtd_cols

            table = Table(data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]))

            doc.build([table])
            self._show_success("Salas exportadas para PDF com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {e}")