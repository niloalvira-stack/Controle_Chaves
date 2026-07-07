import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import config  # Vamos usar o arquivo de configurações para não deixar dados expostos

def enviar_email(destinatario: str, assunto: str, corpo: str) -> bool:
    """
    Envia e-mail usando servidor SMTP configurado.
    Retorna True se enviado com sucesso, False em caso de erro.
    """
    # Carrega configurações do arquivo config.py
    smtp_server = config.SMTP_SERVER
    smtp_port = config.SMTP_PORT
    smtp_usuario = config.SMTP_USUARIO
    smtp_senha = config.SMTP_SENHA
    remetente = config.EMAIL_REMETENTE

    if not all([smtp_server, smtp_port, smtp_usuario, smtp_senha, remetente]):
        raise ValueError("Configurações de e-mail incompletas no arquivo config.py")

    try:
        # Monta a mensagem
        mensagem = MIMEMultipart()
        mensagem["From"] = remetente
        mensagem["To"] = destinatario
        mensagem["Subject"] = assunto
        mensagem["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S -0300")

        # Adiciona o corpo do texto
        mensagem.attach(MIMEText(corpo, "plain", "utf-8"))

        # Conecta ao servidor SMTP
        if smtp_port == 465:
            # Conexão segura com SSL
            servidor = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        else:
            # Conexão comum, depois usa STARTTLS
            servidor = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            servidor.ehlo()
            servidor.starttls()  # Ativa criptografia
            servidor.ehlo()

        # Faz login
        servidor.login(smtp_usuario, smtp_senha)

        # Envia o e-mail
        servidor.sendmail(remetente, destinatario, mensagem.as_string())

        # Fecha a conexão
        servidor.quit()
        return True

    except smtplib.SMTPAuthenticationError:
        raise Exception("Falha de autenticação: verifique usuário e senha do e-mail")
    except smtplib.SMTPConnectError:
        raise Exception("Não foi possível conectar ao servidor SMTP")
    except Exception as e:
        raise Exception(f"Erro ao enviar e-mail: {str(e)}")