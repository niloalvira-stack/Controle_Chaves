# database_init.py
"""
Script de criação/atualização do schema no PostgreSQL.

Use:
    python database_init.py
"""

import os

# limpa variáveis de ambiente que podem injetar DSN/serviços com encoding estranho
for var in ("PGSERVICE", "PGSERVICEFILE", "PGPASSWORD", "PGHOST", "PGDATABASE", "PGUSER"):
    os.environ.pop(var, None)

import psycopg  # psycopg3
from utils.config_app import get_db_config  # <- usar o mesmo config.ini


def get_db_connection():
    """
    Conexão com PostgreSQL usando os dados do config.ini.
    """
    cfg = get_db_config()
    return psycopg.connect(
        host=cfg["host"],
        port=cfg["port"],
        dbname=cfg["database"],
        user=cfg["user"],
        password=cfg["password"],
    )


def init_database():
    conn = get_db_connection()
    cur = conn.cursor()

    # --- TABELA usuarios (login do sistema) ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            login VARCHAR(100) UNIQUE NOT NULL,
            nome  VARCHAR(200) NOT NULL,
            senha VARCHAR(255) NOT NULL,
            primeiro_login BOOLEAN DEFAULT TRUE,
            is_admin       BOOLEAN DEFAULT FALSE
        )
    """)

    # --- TABELA utilizadores (quem retira a chave) ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS utilizadores (
            id SERIAL PRIMARY KEY,
            nome  VARCHAR(200) NOT NULL,
            email VARCHAR(200),
            ativo BOOLEAN DEFAULT TRUE
        )
    """)

    cur.execute("""
        ALTER TABLE utilizadores
        ADD COLUMN IF NOT EXISTS ativo BOOLEAN DEFAULT TRUE
    """)

    # --- TABELA predios ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predios (
            id   SERIAL PRIMARY KEY,
            nome VARCHAR(200) NOT NULL UNIQUE
        )
    """)

    # --- TABELA anexos ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS anexos (
            id        SERIAL PRIMARY KEY,
            nome      VARCHAR(200) NOT NULL,
            predio_id INTEGER,
            CONSTRAINT fk_anexos_predio
                FOREIGN KEY (predio_id)
                REFERENCES predios(id)
                ON DELETE SET NULL
        )
    """)

    # --- TABELA salas ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS salas (
            id        SERIAL PRIMARY KEY,
            nome      VARCHAR(200) NOT NULL,
            descricao TEXT,
            predio_id INTEGER,
            anexo_id  INTEGER,
            status    VARCHAR(50) DEFAULT 'disponivel',
            CONSTRAINT fk_salas_predio
                FOREIGN KEY (predio_id)
                REFERENCES predios(id)
                ON DELETE SET NULL,
            CONSTRAINT fk_salas_anexo
                FOREIGN KEY (anexo_id)
                REFERENCES anexos(id)
                ON DELETE SET NULL
        )
    """)

    # --- TABELA movimentacoes ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id            SERIAL PRIMARY KEY,
            chave         VARCHAR(200) NOT NULL,
            usuario       VARCHAR(200),
            email         VARCHAR(200),
            data_retirada TIMESTAMP,
            data_retorno  TIMESTAMP,
            status        VARCHAR(50) DEFAULT 'disponível',
            alerta_enviado BOOLEAN DEFAULT FALSE,
            utilizador_id  INTEGER,
            CONSTRAINT fk_movimentacoes_utilizador
                FOREIGN KEY (utilizador_id)
                REFERENCES utilizadores(id)
                ON DELETE SET NULL
        )
    """)

    cur.execute("""
        ALTER TABLE movimentacoes
        ADD COLUMN IF NOT EXISTS utilizador_id INTEGER
    """)

    try:
        cur.execute("""
            ALTER TABLE movimentacoes
            ADD CONSTRAINT fk_movimentacoes_utilizador
            FOREIGN KEY (utilizador_id)
            REFERENCES utilizadores(id)
            ON DELETE SET NULL
        """)
    except Exception:
        conn.rollback()
        conn = get_db_connection()
        cur = conn.cursor()

    conn.commit()
    conn.close()
    print("Schema PostgreSQL criado/atualizado com sucesso.")


if __name__ == "__main__":
    init_database()
