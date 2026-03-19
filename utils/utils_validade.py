# utils/utils_validade.py
from datetime import date
from utils.utils_log import log_acao
from db import get_db_connection   # ajuste para o módulo que você já usa

def verificar_expirados():
    """Desativa usuários com data_fim_validade vencida (exceto Servidor)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE utilizadores 
        SET ativo = FALSE
        WHERE vinculo <> 'Servidor'
          AND data_fim_validade IS NOT NULL
          AND data_fim_validade < CURRENT_DATE
          AND ativo = TRUE
        RETURNING id, nome, vinculo, data_fim_validade
    """)
    expirados = cursor.fetchall()
    conn.commit()

    for uid, nome, vinculo, data_fim in expirados:
        log_acao(
            acao="AUTO_DESATIVACAO",
            mensagem=f"{vinculo} '{nome}' (ID={uid}) desativado por expiração em {data_fim}.",
        )

    return len(expirados)
