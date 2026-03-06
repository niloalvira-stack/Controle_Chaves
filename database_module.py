import base64
import psycopg2
import psycopg2.extras
from utils.config_app import get_db_config


def _decode_password(password_b64: str) -> str:
    return base64.b64decode(password_b64).decode("utf-8")


def get_connection():
    """
    Abre conexão com PostgreSQL usando os dados do config.ini
    (senha em base64) e cursor como RealDictCursor.
    """
    cfg = get_db_config()

    try:
        password = _decode_password(cfg["password_b64"])

        conn = psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            dbname=cfg["database"],
            user=cfg["user"],
            password=password,
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        return conn
    except psycopg2.Error as e:
        print(f"Erro ao conectar no banco de dados: {e}")
        return None


def execute_query(query, params=(), fetchone=False, fetchall=False):
    conn = get_connection()
    if conn is None:
        return None

    try:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()

        if fetchone:
            return cur.fetchone()
        if fetchall:
            return cur.fetchall()
        return None
    except psycopg2.Error as e:
        print(f"Erro ao executar query: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()
