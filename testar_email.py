from utils.email_service import enviar_email

try:
    print("Enviando e-mail de teste...")
    sucesso = enviar_email(
        destinatario = "nilo.alvira@alvorada.ifrs.edu.br",  # SEU e-mail CORRETO
        assunto = "✅ Teste envio e-mail Controle de Chaves",
        corpo = "Olá!\n\nSe este e-mail chegou, está tudo funcionando perfeitamente.\n\nAtenciosamente,\nSistema Controle de Chaves"
    )
    print("✅ E-mail enviado com sucesso!")
except Exception as erro:
    print(f"❌ Erro: {erro}")