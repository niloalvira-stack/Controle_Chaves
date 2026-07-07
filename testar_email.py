from utils.email_service import enviar_email

try:
    enviar_email(
        destinatario = "nilo.alvira@alvorada.ifrs.edu.br",
        assunto = "Teste de envio - Sistema de Controle de Chaves",
        corpo = "Se recebeu este e-mail, a configuração está funcionando corretamente!"
    )
    print("✅ E-mail enviado com sucesso!")
except Exception as e:
    print(f"❌ Erro: {e}")