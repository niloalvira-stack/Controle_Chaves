import sqlite3
import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "controle_chaves.db")

def init_database(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            senha TEXT NOT NULL,
            primeiro_login INTEGER DEFAULT 1,
            is_admin INTEGER DEFAULT 0
        )''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT NOT NULL,
            usuario TEXT NOT NULL,
            data_retirada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_retorno TIMESTAMP,
            status TEXT DEFAULT 'disponível'
        )''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            endereco TEXT
        )''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            predio_id INTEGER,
            FOREIGN KEY (predio_id) REFERENCES predios(id)
        )''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anexos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            predio_id INTEGER,
            FOREIGN KEY (predio_id) REFERENCES predios(id)
        )''')

    conn.commit()
    conn.close()
    print("Banco de dados inicializado e tabelas criadas.")

if __name__ == "__main__":
    init_database()
