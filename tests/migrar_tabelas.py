import sqlite3

DB_NAME = "controle_chaves.db"

def migrar_usuarios():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Renomeia a tabela antiga
    cursor.execute("ALTER TABLE usuarios RENAME TO usuarios_old;")

    # Cria a nova tabela com as colunas corretas
    cursor.execute('''
    CREATE TABLE usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT UNIQUE NOT NULL,
        nome TEXT NOT NULL,
        senha TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        primeiro_acesso INTEGER DEFAULT 1,
        data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # Copia dados da tabela antiga para a nova, sem os campos novos
    cursor.execute('''
    INSERT INTO usuarios (id, login, nome, senha, is_admin)
    SELECT id, login, nome, senha, is_admin FROM usuarios_old;
    ''')

    # Remove a tabela antiga
    cursor.execute("DROP TABLE usuarios_old;")

    conn.commit()
    conn.close()
    print("Migração da tabela usuarios concluída.")

def migrar_movimentacoes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("ALTER TABLE movimentacoes RENAME TO movimentacoes_old;")

    cursor.execute('''
    CREATE TABLE movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sala_id INTEGER NOT NULL,
        usuario TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('disponível', 'retirada')),
        data DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sala_id) REFERENCES salas(id) ON DELETE CASCADE
    );
    ''')

    cursor.execute('''
    INSERT INTO movimentacoes (id, usuario, status, data)
    SELECT id, usuario, status, data FROM movimentacoes_old;
    ''')

    cursor.execute("DROP TABLE movimentacoes_old;")

    conn.commit()
    conn.close()
    print("Migração da tabela movimentacoes concluída.")

if __name__ == "__main__":
    migrar_usuarios()
    migrar_movimentacoes()
