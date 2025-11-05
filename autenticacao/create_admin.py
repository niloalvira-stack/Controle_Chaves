from database_init import init_database
init_database()
# o banco será criado SEMPRE no local correto.

from autenticacao import create_user, get_user_by_login, show_info, show_warning

def create_admin_user():
    print("=== Criação de Usuário Admin ===")

    # Verifica se admin já existe
    existing_admin = get_user_by_login("admin")
    if existing_admin:
        show_warning("Aviso", "Usuário admin já existe!")
        return

    # Solicita dados para criação do admin
    login_admin = input("Login do Admin: ").strip()
    senha_admin = input("Senha do Admin: ").strip()
    nome_admin = input("Nome do Admin: ").strip()

    # Validações simples
    if not login_admin or not senha_admin or not nome_admin:
        show_warning("Erro", "Login, senha e nome são obrigatórios.")
        return

    # Cria usuário admin no banco
    create_user(login_admin, nome_admin, senha_admin, is_admin=1)
    show_info("Sucesso", f"Usuário admin '{login_admin}' criado com sucesso!")

if __name__ == "__main__":
    create_admin_user()