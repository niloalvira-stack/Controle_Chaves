# autenticacao/session.py

import time
import traceback
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

    def _normalizar_row_usuario(self, row) -> Optional[Dict[str, Any]]:
        if not row:
            return None

        if isinstance(row, dict):
            return {
                "id": row.get("id"),
                "login": row.get("login"),
                "nome": row.get("nome"),
                "is_admin": row.get("is_admin", False),
            }

        if isinstance(row, (tuple, list)):
            if len(row) < 4:
                return None
            return {
                "id": row[0],
                "login": row[1],
                "nome": row[2],
                "is_admin": row[3],
            }

        return None

    def login(self, login: str) -> bool:
        try:
            if isinstance(login, bytes):
                login = login.decode("utf-8", errors="ignore")

            login = str(login).strip()
            if not login:
                print("SESSION: login vazio.")
                return False

            sql = """
                SELECT id, login, nome, is_admin
                FROM usuarios
                WHERE login = %s
            """
            row = execute_query(sql, (login,), fetchone=True)

            print("SESSION LOGIN RECEBIDO:", repr(login))
            print("SESSION ROW RETORNADA:", row)

        except Exception as e:
            traceback.print_exc()
            print(f"ERRO ao buscar usuário para login '{login}': {type(e).__name__}: {e}")
            log_acao(f"Erro ao buscar usuário para login '{login}': {type(e).__name__}: {e}")
            return False

        dados = self._normalizar_row_usuario(row)
        print("SESSION DADOS NORMALIZADOS:", dados)

        if not dados:
            print(f"SESSION: usuário inexistente na sessão: {login!r}")
            log_acao(f"Tentativa de login com usuário inexistente na sessão: '{login}'")
            return False

        login_db = dados.get("login")
        nome_db = dados.get("nome")

        if isinstance(login_db, bytes):
            login_db = login_db.decode("utf-8", errors="ignore")
        if isinstance(nome_db, bytes):
            nome_db = nome_db.decode("utf-8", errors="ignore")

        if login_db is None:
            login_db = ""
        if nome_db is None:
            nome_db = ""

        valor_is_admin = dados.get("is_admin", False)
        if isinstance(valor_is_admin, str):
            is_admin_flag = valor_is_admin.strip().lower() in ("1", "true", "t", "sim", "yes")
        else:
            is_admin_flag = bool(valor_is_admin)

        try:
            user_id = int(dados.get("id"))
        except (TypeError, ValueError):
            print(f"SESSION: ID inválido: {dados.get('id')!r}")
            log_acao(f"ID inválido ao carregar sessão do usuário '{login}': {dados.get('id')}")
            return False

        self.current_user = SessionUser(
            id=user_id,
            login=str(login_db),
            nome=str(nome_db),
            is_admin=is_admin_flag,
        )
        self.user_login = str(login_db)
        self.is_admin = is_admin_flag
        self.login_time = time.time()
        self.last_activity = time.time()

        print("SESSION current_user:", self.current_user)
        log_acao(f"Sessão iniciada para usuário '{self.user_login}'")
        return True

    def logout(self) -> None:
        if self.user_login:
            log_acao(f"Usuário '{self.user_login}' fez logout da sessão")

        self.current_user = None
        self.user_login = None
        self.is_admin = False
        self.login_time = None
        self.last_activity = None

    def is_logged_in(self) -> bool:
        return self.current_user is not None

    def touch(self) -> None:
        if self.current_user:
            self.last_activity = time.time()

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        if not self.current_user:
            return None
        return asdict(self.current_user)

    def get_user_id(self) -> Optional[int]:
        return self.current_user.id if self.current_user else None

    def get_user_login(self) -> Optional[str]:
        return self.current_user.login if self.current_user else None


session_manager = SessionManager()


def validar_login(login: str) -> bool:
    return session_manager.login(login)


def get_current_user() -> Optional[Dict[str, Any]]:
    return session_manager.get_user_info()


def is_admin() -> bool:
    return session_manager.is_admin


def get_user_id() -> Optional[int]:
    return session_manager.get_user_id()


def get_user_login() -> Optional[str]:
    return session_manager.get_user_login()