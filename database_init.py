# database_init.py

import os
import sqlite3

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "controle_chaves.db")


def init_database(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Tabela de usuários (login do sistema)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            senha TEXT NOT NULL,
            primeiro_login INTEGER DEFAULT 1,
            is_admin INTEGER DEFAULT 0
        )
    """)

    # Tabela de utilizadores (quem retira a chave)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilizadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome  TEXT NOT NULL,
            email TEXT,
            ativo INTEGER DEFAULT 1
        )
    """)

    # Garante coluna ativo em bases antigas
    cursor.execute("PRAGMA table_info(utilizadores)")
    cols = [r[1] for r in cursor.fetchall()]
    if "ativo" not in cols:
        cursor.execute("ALTER TABLE utilizadores ADD COLUMN ativo INTEGER DEFAULT 1")

    # Tabela de prédios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)

    # Tabela de anexos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anexos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            predio_id INTEGER,
            FOREIGN KEY (predio_id) REFERENCES predios(id)
        )
    """)

    # Tabela de salas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS salas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            predio_id INTEGER,
            anexo_id INTEGER,
            status TEXT DEFAULT 'disponivel',
            FOREIGN KEY (predio_id) REFERENCES predios(id),
            FOREIGN KEY (anexo_id) REFERENCES anexos(id)
        )
    """)

    # Tabela de movimentações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT NOT NULL,
            usuario TEXT,
            email TEXT,
            data_retirada TIMESTAMP,
            data_retorno TIMESTAMP,
            status TEXT DEFAULT 'disponível',
            alerta_enviado INTEGER DEFAULT 0
        )
    """)

    # Garante coluna utilizador_id
    cursor.execute("PRAGMA table_info(movimentacoes)")
    cols = [r[1] for r in cursor.fetchall()]
    if "utilizador_id" not in cols:
        cursor.execute("ALTER TABLE movimentacoes ADD COLUMN utilizador_id INTEGER")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_database()
