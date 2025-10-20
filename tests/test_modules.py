# tests/test_modules.py

from database_module import execute_query
from database_init import initialize_database

def teste_predios():
    print("=== Teste: Prédios ===")
    # Inserir prédio de teste
    execute_query("INSERT INTO predios (nome) VALUES (?)", ("Prédio Teste",))
    predio = execute_query("SELECT * FROM predios WHERE nome=?", ("Prédio Teste",), fetchall=True)
    if predio:
        print(f"✅ Prédio encontrado: {predio[0]}")
    else:
        print("❌ Falha: Prédio não encontrado.")

def teste_anexos():
    print("\n=== Teste: Anexos ===")
    # Inserir anexo de teste
    execute_query("INSERT INTO anexos (nome, predio_id) VALUES (?, ?)", ("Anexo Teste", 1))
    anexos = execute_query("SELECT * FROM anexos WHERE nome=?", ("Anexo Teste",), fetchall=True)
    if anexos:
        print(f"✅ Anexo encontrado: {anexos[0]}")
    else:
        print("❌ Falha: Anexo não encontrado.")

def teste_salas():
    print("\n=== Teste: Salas ===")
    # Inserir sala de teste
    execute_query("INSERT INTO salas (nome, predio_id, anexo_id) VALUES (?, ?, ?)", ("Sala Teste", 1, 1))
    salas = execute_query("SELECT * FROM salas WHERE nome=?", ("Sala Teste",), fetchall=True)
    if salas:
        print(f"✅ Sala encontrada: {salas[0]}")
    else:
        print("❌ Falha: Sala não encontrada.")

def teste_movimentacoes():
    print("\n=== Teste: Movimentações ===")
    # Inserir movimentação de teste
    try:
        execute_query(
            "INSERT INTO movimentacoes (usuario_nome, sala_nome, tipo, data) VALUES (?, ?, ?, datetime('now'))",
            ("admin", "Sala Teste", "retirada")
        )
    except Exception as e:
        print(f"[ERRO SQLITE] {e}")

    try:
        movs = execute_query(
            "SELECT * FROM movimentacoes WHERE usuario_nome=?",
            ("admin",),
            fetchall=True
        )
        if movs:
            print(f"✅ Movimentação encontrada: {movs[0]}")
        else:
            print("❌ Nenhuma movimentação encontrada para o admin.")
    except Exception as e:
        print(f"[ERRO SQLITE] {e}")

if __name__ == "__main__":
    print("✅ Banco de dados inicializado com sucesso!")
    initialize_database()

    teste_predios()
    teste_anexos()
    teste_salas()
    teste_movimentacoes()
