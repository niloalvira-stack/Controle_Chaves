from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
import base64
from io import BytesIO
from .qrcode_helper import gerar_qrcode_etiqueta


def gerar_etiqueta_pdf(caminho_arquivo, lista_chaves):
    """
    Gera PDF com etiquetas em LOTE (várias de uma vez)
    lista_chaves = [{"id": X, "etiqueta": "...", "sala_nome": "...", "tipo_chave": "..."}]
    """
    doc = SimpleDocTemplate(caminho_arquivo, pagesize=A4,
                            leftMargin=1 * cm, rightMargin=1 * cm,
                            topMargin=1 * cm, bottomMargin=1 * cm)
    estilo = getSampleStyleSheet()["Normal"]
    estilo.fontSize = 9
    estilo.leading = 11

    elementos = []

    for ch in lista_chaves:
        b64, dados_qr = gerar_qrcode_etiqueta(
            ch["id"], ch["etiqueta"], ch["sala_nome"], ch["tipo_chave"]
        )

        img_qr = Image(BytesIO(base64.b64decode(b64)), width=3 * cm, height=3 * cm)

        elementos.append(img_qr)
        elementos.append(Paragraph(f"<b>{ch['etiqueta']}</b>", estilo))
        elementos.append(Paragraph(f"Sala: {ch['sala_nome']}", estilo))
        elementos.append(Paragraph(f"ID: {ch['id']} | {ch['tipo_chave'].upper()}", estilo))
        elementos.append(Spacer(1, 0.5 * cm))
        elementos.append(Spacer(1, 0.15 * cm))

    doc.build(elementos)
    return caminho_arquivo


# ✅ FUNÇÃO NOVA: Gera UMA etiqueta individualmente
def gerar_etiqueta_unica(caminho_arquivo, chave):
    """
    Gera PDF com UMA ÚNICA etiqueta — para uso individual quando precisar
    chave = {"id": X, "etiqueta": "...", "sala_nome": "...", "tipo_chave": "..."}
    """
    doc = SimpleDocTemplate(caminho_arquivo, pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=3 * cm, bottomMargin=3 * cm)

    estilo = getSampleStyleSheet()["Normal"]
    estilo.fontSize = 11
    estilo.leading = 14

    elementos = []

    b64, dados_qr = gerar_qrcode_etiqueta(
        chave["id"], chave["etiqueta"], chave["sala_nome"], chave["tipo_chave"]
    )

    img_qr = Image(BytesIO(base64.b64decode(b64)), width=4 * cm, height=4 * cm)
    elementos.append(img_qr)
    elementos.append(Spacer(1, 0.8 * cm))

    elementos.append(Paragraph(f"<b>{ch['etiqueta']}</b>", estilo))
    elementos.append(Paragraph(f"Sala: {ch['sala_nome']}", estilo))
    elementos.append(Paragraph(f"ID: {ch['id']} | {ch['tipo_chave'].upper()}", estilo))

    doc.build(elementos)
    return caminho_arquivo