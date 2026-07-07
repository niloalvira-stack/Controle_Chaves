# autenticacao/auth_models.py

from autenticacao.autenticacao import get_user_by_login, verify_password
from autenticacao.session import session_manager


def autenticar_usuario(login, senha):
    try:
        user = get_user_by_login(login)
        if not user:
            return None

        if not verify_password(user["senha"], senha):
            return None

        if not session_manager.login(str(user["login"])):
            return None

        tipo_usuario = "admin" if bool(user["is_admin"]) else "operador"
        ativo = True

        return (user["id"], user["nome"], user["login"], tipo_usuario, ativo)

    except Exception as e:
        print(f"Erro ao autenticar usuário: {e}")
        return None


def buscar_usuario_por_username(login):
    try:
        user = get_user_by_login(login)
        if not user:
            return None

        return (user["id"], user["nome"], user["login"], None)
    except Exception as e:
        print(f"Erro ao buscar usuário: {e}")
        return None


def solicitar_recuperacao_senha(user_id, email):
    print("Recuperação de senha ainda não implementada para esta estrutura.")
    return False


def obter_usuario(user_id):
    user = session_manager.current_user
    if user and user.id == user_id:
        tipo_usuario = "admin" if bool(user.is_admin) else "operador"
        ativo = True
        return (user.id, user.nome, user.login, tipo_usuario, ativo)
    return None