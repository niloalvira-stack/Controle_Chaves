import qrcode
import base64
from io import BytesIO
from PIL import Image
from pyzbar.pyzbar import decode
from PyQt6.QtGui import QPixmap, QImage
import cv2  # ✅ Importação que estava faltando!


def gerar_qrcode_etiqueta(chave_id, etiqueta, sala_nome, tipo_chave):
    """Gera QR Code codificado em Base64 com dados da chave"""
    dados = f"CHAVE|{chave_id}|{etiqueta}|{sala_nome}|{tipo_chave}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(dados)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return b64, dados


def gerar_qrcode_pixmap(chave_id, etiqueta, sala_nome, tipo_chave):
    """Gera QR Code como QPixmap para exibir na tela"""
    b64, dados = gerar_qrcode_etiqueta(chave_id, etiqueta, sala_nome, tipo_chave)
    dados_imagem = base64.b64decode(b64)
    img = Image.open(BytesIO(dados_imagem)).convert("RGB")

    qimg = QImage(img.tobytes(), img.width, img.height, img.width * 3, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg), dados


def ler_qrcode_dados(dados_qr):
    """Decodifica o texto lido do QR Code em dicionário"""
    if not dados_qr or not dados_qr.startswith("CHAVE|"):
        return None
    partes = dados_qr.split("|")
    if len(partes) >= 5:
        return {
            "tipo": partes[0],
            "chave_id": int(partes[1]),
            "etiqueta": partes[2],
            "sala_nome": partes[3],
            "tipo_chave": partes[4]
        }
    return None


def decodificar_imagem_qr(imagem_pil):
    """Lê QR Code de uma imagem (para câmera ou arquivo)"""
    resultados = decode(imagem_pil)
    if resultados:
        return resultados[0].data.decode("utf-8").strip()
    return None


# ═══════ FUNÇÃO PARA WEBCAM ═══════
def ler_qrcode_frame_cv2(frame_cv2):
    """
    Recebe um frame da câmera OpenCV (formato BGR),
    converte para PIL e lê o QR Code
    """
    # Converte BGR (OpenCV) → RGB (PIL)
    frame_rgb = cv2.cvtColor(frame_cv2, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(frame_rgb)
    return decodificar_imagem_qr(img_pil)