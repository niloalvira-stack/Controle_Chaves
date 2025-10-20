import sqlite3

def listar_usuarios(db_path="controle_chaves.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, login, nome, is_admin FROM usuarios ORDER BY id;")
    usuarios = cursor.fetchall()
    conn.close()

    if not usuarios:
        print("Nenhum usuário encontrado na base.")
    else:
        print("Usuários cadastrados no sistema:")
        for u in usuarios:
            print(f"ID: {u[0]} | Login: {u[1]} | Nome: {u[2]} | Admin: {'Sim' if u[3] else 'Não'}")

if __name__ == "__main__":
    listar_usuarios()
