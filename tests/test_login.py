from database_module import execute_query
from utils import hash_password

def test_admin_login():
    """Testa se o usuário admin existe e se o login é válido."""
    print("=== Teste: Login do admin ===")
    user = execute_query(
        "SELECT id, username, password, is_admin FROM usuarios WHERE username = ?",
        ("admin",),
        fetchone=True
    )
    if not user:
        print("Falha: Usuário admin não encontrado.")
        return False

    user_id, username, stored_password, is_admin = user

    if stored_password == hash_password("admin"):
        print("Sucesso: Login admin válido.")
        return True
    else:
        print("Falha: Senha do admin incorreta.")
        return False

def test_wrong_password():
    """Testa login com senha errada."""
    print("\n=== Teste: Login com senha errada ===")
    user = execute_query(
        "SELECT id, username, password FROM usuarios WHERE username = ?",
        ("admin",),
        fetchone=True
    )
    if not user:
        print("Falha: Usuário admin não encontrado.")
        return False

    _, _, stored_password = user
    if stored_password != hash_password("errada"):
        print("Sucesso: Sistema bloqueou senha incorreta.")
        return True
    else:
        print("Falha: Aceitou senha incorreta.")
        return False

def test_nonexistent_user():
    """Testa login com usuário inexistente."""
    print("\n=== Teste: Usuário inexistente ===")
    user = execute_query(
        "SELECT id FROM usuarios WHERE username = ?",
        ("naoexiste",),
        fetchone=True
    )
    if not user:
        print("Sucesso: Usuário inexistente não encontrado.")
        return True
    else:
        print("Falha: Usuário inexistente encontrado.")
        return False

if __name__ == "__main__":
    test_admin_login()
    test_wrong_password()
    test_nonexistent_user()
