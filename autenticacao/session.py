# autenticacao/session.py

import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

from database_module import execute_query
from utils.utils_log import log_acao


@dataclass
class SessionUser:
    id: int
    login: str
    nome: str
    is_admin: bool


class SessionManager:
    def __init__(self) -> None:
        self.current_user: Optional[SessionUser] = None
        self.user_login: Optional[str] = None
        self.is_admin: bool = False
        self.login_time: Optional[float] = None
        self.last_activity: Optional[float] = None

    # ------------------------------------------------------------------
    # Login / Logout
    # ------------------------------------------------------------------
    def login(self, login: str) -> bool:
        """
        Carrega os dados do usuário a partir do banco (tabela usuarios)
        e preenche a sessão global, incluindo o flag is_admin.
        """
        try:
            sql = """
                SELECT id, login, nome, is_admin
                FROM usuarios
                WHERE login = %s
            """
            row = execute_query(sql, (login,), fetchone=True)
        except Exception as e:
            log_acao(f"Erro ao buscar usuário para login '{login}': {e}")
            return False

        if not row:
            log_acao(f"Tentativa de login com usuário inexistente na sessão: '{login}'")
            return False

        # execute_query com RealDictCursor já retorna dict
        user = dict(row)
        is_admin_flag = bool(user.get("is_admin", False))

        self.current_user = SessionUser(
            id=user["id"],
            login=user["login"],
            nome=user["nome"],
            is_admin=is_admin_flag,
        )
        self.user_login = user["login"]
        self.is_admin = is_admin_flag
        self.login_time = time.time()
        self.last_activity = time.time()
        return True

    def logout(self) -> None:
        if self.user_login:
            log_acao(f"Usuário '{self.user_login}' fez logout da sessão")
        self.current_user = None
        self.user_login = None
        self.is_admin = False
        self.login_time = None
        self.last_activity = None

    # ------------------------------------------------------------------
    # Informações da sessão
    # ------------------------------------------------------------------
    def is_logged_in(self) -> bool:
        return self.current_user is not None

    def touch(self) -> None:
        """Atualiza timestamp da última atividade."""
        if self.current_user:
            self.last_activity = time.time()

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Retorna um dicionário com dados do usuário atual ou None."""
        if not self.current_user:
            return None
        return asdict(self.current_user)

    # ------------------------------------------------------------------
    # Atalhos para campos específicos
    # ------------------------------------------------------------------
    def get_user_id(self) -> Optional[int]:
        return self.current_user.id if self.current_user else None

    def get_user_login(self) -> Optional[str]:
        return self.current_user.login if self.current_user else None


# Instância global da sessão
session_manager = SessionManager()


# Funções de atalho usadas pelo resto da aplicação
def validar_login(login: str) -> bool:
    """
    Função de atalho usada pela tela de login.
    Apenas delega para session_manager.login(login).
    """
    return session_manager.login(login)


def get_current_user() -> Optional[Dict[str, Any]]:
    return session_manager.get_user_info()


def is_admin() -> bool:
    return session_manager.is_admin


def get_user_id() -> Optional[int]:
    return session_manager.get_user_id()


def get_user_login() -> Optional[str]:
    return session_manager.get_user_login()
