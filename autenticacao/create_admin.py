from autenticacao import create_user, get_user_by_login

def create_admin_user():
    print("=== Criação de Usuário Admin ===")

    # Verifica se admin já existe
    existing_admin = get_user_by_login("admin")
    if existing_admin:
        print("Usuário admin já existe!")
        return

    login_admin = input("Login do Admin: ").strip()
    senha_admin = input("Senha do Admin: ").strip()
    nome_admin = input("Nome do Admin: ").strip()

    if not login_admin or not senha_admin or not nome_admin:
        print("Login, senha e nome são obrigatórios.")
        return

    create_user(login_admin, nome_admin, senha_admin, is_admin=True)
    print(f"Usuário admin '{login_admin}' criado com sucesso!")

if __name__ == "__main__":
    create_admin_user()
