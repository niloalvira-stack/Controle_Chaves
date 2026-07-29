import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from utils.config_app import get_email_config
from database_module import get_connection  # Importa a conexão igual no resto do sistema

def enviar_email(destinatario: str, assunto: str, corpo: str, movimentacao_id: int = None) -> bool:
    """
    Envia e-mail e opcionalmente marca como enviado na movimentação.
    Retorna True se enviado com sucesso, False em caso de erro.
    """
    cfg = get_email_config()
    smtp_server = cfg["smtp_server"]
    smtp_port = cfg["smtp_port"]
    smtp_usuario = cfg["smtp_usuario"]
    smtp_senha = cfg["smtp_senha"]
    remetente = cfg["email_remetente"]

    if not all([smtp_server, smtp_port, smtp_usuario, smtp_senha, remetente]):
        raise ValueError("Configurações de e-mail incompletas no arquivo config.ini")

    try:
        mensagem = MIMEMultipart()
        mensagem["From"] = remetente
        mensagem["To"] = destinatario
        mensagem["Subject"] = assunto
        mensagem["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S -0300")
        mensagem.attach(MIMEText(corpo, "plain", "utf-8"))

        if smtp_port == 465:
            servidor = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        else:
            servidor = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            servidor.ehlo()
            servidor.starttls()
            servidor.ehlo()

        servidor.login(smtp_usuario, smtp_senha)
        servidor.sendmail(remetente, destinatario, mensagem.as_string())
        servidor.quit()

        # ✅ SE TIVER O ID, MARCA COMO ENVIADO NO BANCO
        if movimentacao_id is not None:
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE movimentacoes
                    SET email_aviso_atraso_enviado = TRUE
                    WHERE id = %s
                """, (movimentacao_id,))
                conn.commit()
            finally:
                conn.close()

        return True

    except smtplib.SMTPAuthenticationError:
        raise Exception("Falha de autenticação: verifique usuário e senha de app do Gmail")
    except smtplib.SMTPConnectError:
        raise Exception("Não foi possível conectar ao servidor SMTP")
    except Exception as e:
        raise Exception(f"Erro ao enviar e-mail: {str(e)}")