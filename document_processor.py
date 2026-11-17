"""
Fügt die variierte Unterschrift zufällig innerhalb des in config.py
definierten Kästchens ein.
"""
import io
import random
import fitz  # PyMuPDF
from PIL import Image

import config


def render_pdf_page_to_png(pdf_bytes: bytes, page_index: int, dpi: int = 150) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(page_index)
    zoom = dpi / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    png = pix.tobytes("png")
    doc.close()
    return png


def _berechne_platzierung(signature_png: bytes):
    """
    Berechnet eine zufällige Position innerhalb des Kästchens.
    Gibt (x_pt, y_pt, breite_pt, hoehe_pt) in PDF-Punkten zurück.
    """
    kaestchen_w = config.KAESTCHEN_X1 - config.KAESTCHEN_X0
    kaestchen_h = config.KAESTCHEN_Y1 - config.KAESTCHEN_Y0

    breite_pt = kaestchen_w * config.SIGNATUR_BREITE_FAKTOR

    sig = Image.open(io.BytesIO(signature_png))
    aspect = sig.height / sig.width
    hoehe_pt = breite_pt * aspect

    max_hoehe = kaestchen_h * config.SIGNATUR_HOEHE_FAKTOR
    if hoehe_pt > max_hoehe:
        hoehe_pt = max_hoehe
        breite_pt = hoehe_pt / aspect

    cx = (config.KAESTCHEN_X0 + config.KAESTCHEN_X1) / 2
    cy = (config.KAESTCHEN_Y0 + config.KAESTCHEN_Y1) / 2

    max_dx = kaestchen_w * config.POSITION_VARIANZ_X
    max_dy = kaestchen_h * config.POSITION_VARIANZ_Y
    dx = random.uniform(-max_dx, max_dx)
    dy = random.uniform(-max_dy, max_dy)

    cx += dx
    cy += dy

    x0 = cx - breite_pt / 2
    y0 = cy - hoehe_pt / 2
    x0 = max(config.KAESTCHEN_X0, min(x0, config.KAESTCHEN_X1 - breite_pt))
    y0 = max(config.KAESTCHEN_Y0, min(y0, config.KAESTCHEN_Y1 - hoehe_pt))

    return x0, y0, breite_pt, hoehe_pt


def insert_signature_pdf(
    pdf_bytes: bytes,
    page_index: int,
    signature_png: bytes,
) -> bytes:
    x, y, w, h = _berechne_platzierung(signature_png)

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(page_index)
    rect = fitz.Rect(x, y, x + w, y + h)
    page.insert_image(rect, stream=signature_png, overlay=True)

    out = io.BytesIO()
    doc.save(out, deflate=True)
    doc.close()
    return out.getvalue()
