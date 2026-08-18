import os
import base64
import configparser
from utils.resources import resource_path


CONFIG_FILE = resource_path("config.ini")


def load_config():
    config = configparser.ConfigParser()

    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {CONFIG_FILE}")

    files_read = config.read(CONFIG_FILE, encoding="utf-8")
    if not files_read:
        raise FileNotFoundError(f"Não foi possível ler o arquivo de configuração: {CONFIG_FILE}")

    return config


def require_section(config, section_name):
    if not config.has_section(section_name):
        raise KeyError(f"Seção obrigatória não encontrada no config.ini: [{section_name}]")
    return config[section_name]


def require_option(section, section_name, option_name):
    value = section.get(option_name)
    if value is None or str(value).strip() == "":
        raise ValueError(
            f"Configuração obrigatória ausente ou vazia em [{section_name}]: {option_name}"
        )
    return value.strip()


def get_db_config():
    config = load_config()
    section_name = "postgres"
    postgres = require_section(config, section_name)

    host = require_option(postgres, section_name, "host")
    port = postgres.getint("port")
    database = require_option(postgres, section_name, "database")
    user = require_option(postgres, section_name, "user")
    password_b64 = require_option(postgres, section_name, "password_b64")

    try:
        password = base64.b64decode(password_b64).decode("utf-8")
    except Exception as e:
        raise ValueError("Falha ao decodificar password_b64 da seção [postgres]") from e

    return {
        "host": host,
        "port": port,
        "dbname": database,
        "user": user,
        "password": password,
    }


def get_logs_dir():
    config = load_config()

    if config.has_section("logs") and config.has_option("logs", "base_dir"):
        base_dir = config.get("logs", "base_dir").strip()
        if base_dir:
            return base_dir

    return "logs"


def get_email_config():
    config = load_config()
    section_name = "email"
    email = require_section(config, section_name)

    return {
        "smtp_server": require_option(email, section_name, "smtp_server"),
        "smtp_port": email.getint("smtp_port"),
        "email_remetente": require_option(email, section_name, "email_remetente"),
        "smtp_usuario": require_option(email, section_name, "smtp_usuario"),
        "smtp_senha": require_option(email, section_name, "smtp_senha"),
    }


def get_app_config():
    config = load_config()

    defaults = {
        "app_name": "Controle de Chaves",
        "app_version": "1.1.6",
        "app_developer": "Nilo Alvira",
        "app_company": "IFRS-Campus Alvorada / DTI",
    }

    if not config.has_section("app"):
        return defaults

    app = config["app"]

    return {
        "app_name": app.get("app_name", defaults["app_name"]).strip(),
        "app_version": app.get("app_version", defaults["app_version"]).strip(),
        "app_developer": app.get("app_developer", defaults["app_developer"]).strip(),
        "app_company": app.get("app_company", defaults["app_company"]).strip(),
    }