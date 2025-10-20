from autenticacao import create_user, verify_password, get_user_by_login

def test_create_and_verify():
    login = "testuser"
    nome = "Test User"
    senha = "123456"
    create_user(login, nome, senha)

    user = get_user_by_login(login)
    assert user is not None, "Usuário não encontrado!"
    assert verify_password(user[3], senha), "Senha não confere!"

if __name__ == "__main__":
    test_create_and_verify()
    print("Teste de autenticação ok.")
