from autenticacao import get_user_by_login

def test_admin_user():
    admin = get_user_by_login("admin")
    if admin:
        print("Usuário admin encontrado no banco:")
        print(f"ID: {admin['id']}")
        print(f"Login: {admin['login']}")
        print(f"Nome: {admin['nome']}")
        print(f"É admin? {'Sim' if admin['is_admin'] else 'Não'}")
        print(f"Primeiro login? {'Sim' if admin['primeiro_login'] else 'Não'}")
    else:
        print("Usuário admin NÃO encontrado no banco.")

if __name__ == "__main__":
    test_admin_user()
