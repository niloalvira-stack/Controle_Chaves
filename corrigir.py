# Corrige indentação: converte TODOS os tabs em 4 espaços
caminho = r"C:\Controle_Chaves\controle\movimentacoes.py"

with open(caminho, "r", encoding="utf-8") as f:
    conteudo = f.read()


# Substitui todos os TABs por 4 espaços
conteudo_corrigido = conteudo.replace("\t", "    ")

with open(caminho, "w", encoding="utf-8") as f:
    f.write(conteudo_corrigido)

print("✅ Arquivo corrigido! Tabs convertidos para 4 espaços.")