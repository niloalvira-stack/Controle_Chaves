from PyQt6.QtCore import QThread, pyqtSignal

from autenticacao.helpers_autenticacao import get_db_connection


class QueryThread(QThread):
    loaded = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, sql, params=None, parent=None):
        super().__init__(parent)
        self.sql = sql
        self.params = params or ()

    def run(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(self.sql, self.params)
            rows = cursor.fetchall()
            self.loaded.emit(rows)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if conn:
                conn.close()