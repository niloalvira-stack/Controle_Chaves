import sys
import os

def caminho_recurso(relativo: str) -> str:
    """Caminho correto em desenvolvimento OU compilado"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        # Sobe 1 nível pois esse arquivo está dentro de utils/
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relativo)