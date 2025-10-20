from autenticacao import get_user_by_login, verify_password

def test_verify_admin_password(password_to_test):
    user = get_user_by_login("admin")
    if not user:
        print("Usuário admin não encontrado.")
        return

    stored_hash = user["senha"]
    if verify_password(stored_hash, password_to_test):
        print("Senha válida para usuário admin.")
    else:
        print("Senha inválida para usuário admin.")

if __name__ == "__main__":
    # Substitua 'senha_do_admin' pela senha correta que você usou na criação
    test_verify_admin_password("admin1234")
