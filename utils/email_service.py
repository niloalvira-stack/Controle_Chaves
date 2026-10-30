import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from utils.config_app import get_email_config, get_email_modo_envio  # ✅ Adicionada a nova função
from database_module import get_connection


def enviar_email(destinatario: str, assunto: str, corpo: str, movimentacao_id: int = None) -> bool:
    """
    Envia e-mail respeitando o modo de envio configurado.
    Retorna True se enviado, False se modo Manual.
    """
    # ✅ Verifica o modo atual
    modo = get_email_modo_envio()

    # Se for Manual, NÃO envia automaticamente
    if modo == "Manual":
        return False  # A tela vai saber que precisa exibir o botão manual

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

        mensagem.attach(MIMEText(corpo, "html", "utf-8"))

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

        if movimentacao_id is not None:
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE movimentacoes
                    SET alerta_enviado = TRUE
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