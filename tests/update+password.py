admin
from utils import hash_password
from database_module import execute_query, execute_commit

def atualizar_senha_usuario():
    login = input("Digite o login do usuário para atualizar a senha: ").strip()
    user = execute_query("SELECT id FROM usuarios WHERE login = ?", (login,), fetchone=True)
    if not user:
        print(f"Usuário '{login}' não encontrado.")
        return

    nova_senha = input("Digite a nova senha para o usuário: ").strip()
    novo_hash = hash_password(nova_senha)
    execute_commit("UPDATE usuarios SET senha = ? WHERE id = ?", (novo_hash, user['id']))
    print(f"Senha do usuário '{login}' foi atualizada com sucesso.")

if __name__ == "__main__":
    atualizar_senha_usuario()
