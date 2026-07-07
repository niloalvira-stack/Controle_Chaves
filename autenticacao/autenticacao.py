import bcrypt
import psycopg
import psycopg.rows

from utils.config_app import get_db_config

DB_CONFIG = get_db_config()


def execute_query(query, params=(), fetchone=False):
    """
    Executa query no PostgreSQL.
    - Para SELECT, retorna dict (fetchone=True) ou lista de dicts.
    - Para INSERT/UPDATE/DELETE, retorna None.
    """
    conn = None
    try:
        conn = psycopg.connect(**DB_CONFIG)
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        cur.execute(query, params)

        is_select = query.lstrip().upper().startswith("SELECT")

        if is_select:
            result = cur.fetchone() if fetchone else cur.fetchall()
        else:
            result = None

        conn.commit()
        return result

    except Exception as e:
        print(f"Erro ao executar query: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()


def get_user_by_login(login):
    """
    Busca usuário pelo login.
    Retorna dict com os campos necessários para autenticação ou None.
    """
    if isinstance(login, bytes):
        login = login.decode("utf-8", errors="ignore")

    login = str(login).strip()
    if not login:
        return None

    query = """
        SELECT id, login, nome, senha, primeiro_login, is_admin
        FROM usuarios
        WHERE login = %s
    """
    user = execute_query(query, (login,), fetchone=True)

    if not user:
        return None

    if isinstance(user.get("login"), bytes):
        user["login"] = user["login"].decode("utf-8", errors="ignore")

    if isinstance(user.get("nome"), bytes):
        user["nome"] = user["nome"].decode("utf-8", errors="ignore")

    user["ativo"] = True
    return user


def hash_password(password):
    """
    Gera hash bcrypt da senha.
    """
    if isinstance(password, str):
        password = password.encode("utf-8")
    return bcrypt.hashpw(password, bcrypt.gensalt())


def verify_password(stored_hash, password):
    """
    Verifica se a senha informada corresponde ao hash salvo.
    """
    if stored_hash is None or password is None:
        return False

    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode("utf-8")

    if isinstance(password, str):
        password = password.encode("utf-8")

    try:
        return bcrypt.checkpw(password, stored_hash)
    except Exception as e:
        print(f"Erro ao verificar senha: {e}")
        return False