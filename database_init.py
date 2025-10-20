import sqlite3

def init_database(db_path="controle_chaves.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Criação da tabela usuarios, se não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT UNIQUE NOT NULL,
        nome TEXT NOT NULL,
        senha TEXT NOT NULL,
        primeiro_login INTEGER DEFAULT 1,
        is_admin INTEGER DEFAULT 0
    )
    ''')

    # Criação da tabela movimentacoes, se não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chave TEXT NOT NULL,
        usuario TEXT NOT NULL,
        data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()

    print("Banco de dados inicializado e tabelas criadas.")

if __name__ == "__main__":
    init_database()
