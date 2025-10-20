from database_module import execute_query
import time

class SessionManager:
    def __init__(self):
        self.current_user = None
        self.user_login = None
        self.is_admin = False
        self.login_time = None
        self.last_activity = None

    def login(self, user_login, is_admin):
        try:
            user_data = execute_query(
                "SELECT id, login, nome, is_admin FROM usuarios WHERE login = ?",
                (user_login,), fetchone=True
            )
            if user_data:
                self.current_user = user_data
                self.user_login = user_login
                self.is_admin = bool(is_admin)
                self.login_time = time.time()
                self.last_activity = time.time()
                return True
            return False
        except Exception as e:
            print(f"Erro ao iniciar sessão: {e}")
            return False

    def logout(self):
        self.current_user = None
        self.user_login = None
        self.is_admin = False
        self.login_time = None
        self.last_activity = None

    def is_logged_in(self):
        return self.current_user is not None

    def update_activity(self):
        if self.is_logged_in():
            self.last_activity = time.time()

    def get_session_duration(self):
        if self.login_time:
            return time.time() - self.login_time
        return 0

    def get_idle_time(self):
        if self.last_activity:
            return time.time() - self.last_activity
        return 0

    def get_user_info(self):
        if self.current_user:
            return {
                'id': self.current_user['id'],
                'login': self.current_user['login'],
                'nome': self.current_user['nome'],
                'is_admin': self.is_admin
            }
        return None

session_manager = SessionManager()

def get_current_user():
    return session_manager.get_user_info()

def is_admin():
    return session_manager.is_admin

def is_logged_in():
    return session_manager.is_logged_in()
