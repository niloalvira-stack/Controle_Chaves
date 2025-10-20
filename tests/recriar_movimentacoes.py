import sqlite3

def recriar_tabela_movimentacoes(db_path="controle_chaves.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS movimentacoes;")
    cursor.execute('''
        CREATE TABLE movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT NOT NULL,
            usuario TEXT NOT NULL,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()
    print("Tabela movimentacoes recriada com a estrutura correta.")

if __name__ == "__main__":
    recriar_tabela_movimentacoes()
