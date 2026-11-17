"""
Erzeugt organisch variierende, aber stark originalgetreue Versionen
einer Unterschrift. Alle Parameter werden aus config.py gelesen.
"""
import cv2
import numpy as np
from PIL import Image
import io
import time
import random

import config


def _load_gray(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("Bild konnte nicht gelesen werden.")
    return img


def _extract_ink(gray: np.ndarray) -> np.ndarray:
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 25, 10,
    )
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    return binary


def _crop_to_content(binary: np.ndarray) -> np.ndarray:
    coords = cv2.findNonZero(binary)
    if coords is None:
        return binary
    x, y, w, h = cv2.boundingRect(coords)
    pad = 4
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(binary.shape[1], x + w + pad)
    y1 = min(binary.shape[0], y + h + pad)
    return binary[y0:y1, x0:x1]


def _random_perspective(img: np.ndarray, max_shift: float) -> np.ndarray:
    h, w = img.shape[:2]
    dx = int(w * max_shift)
    dy = int(h * max_shift)
    src = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    dst = np.float32([
        [random.randint(0, dx), random.randint(0, dy)],
        [w - random.randint(0, dx), random.randint(0, dy)],
        [random.randint(0, dx), h - random.randint(0, dy)],
        [w - random.randint(0, dx), h - random.randint(0, dy)],
    ])
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(img, M, (w, h),
                               flags=cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_CONSTANT,
                               borderValue=0)


def _stroke_variation(binary: np.ndarray) -> np.ndarray:
    r = random.random()
    if r < config.STRICH_DILATE_WAHRSCHEINLICHKEIT:
        k = np.ones((2, 2), np.uint8)
        binary = cv2.dilate(binary, k, iterations=1)
    elif r < (config.STRICH_DILATE_WAHRSCHEINLICHKEIT
              + config.STRICH_ERODE_WAHRSCHEINLICHKEIT):
        k = np.ones((2, 2), np.uint8)
        binary = cv2.erode(binary, k, iterations=1)

    blur = cv2.GaussianBlur(binary, (3, 3), 0.4)
    noise = np.random.normal(0, config.RAUSCH_SIGMA, blur.shape).astype(np.int16)
    noisy = np.clip(blur.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return noisy


def _apply_alpha(mask: np.ndarray, color=(15, 15, 40)) -> Image.Image:
    h, w = mask.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., 0] = color[0]
    rgba[..., 1] = color[1]
    rgba[..., 2] = color[2]
    rgba[..., 3] = mask
    return Image.fromarray(rgba, mode="RGBA")


def generate_signature_variant(image_bytes: bytes) -> Image.Image:
    random.seed(time.time_ns())  # <--- HIER MUSS ES HIN
    gray = _load_gray(image_bytes)
    ink = _extract_ink(gray)

    # Rotation – gewünschter Bereich aus config (z. B. ±8°)
    angle = random.uniform(config.ROTATION_MIN_GRAD, config.ROTATION_MAX_GRAD)
    h, w = ink.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    ink = cv2.warpAffine(ink, M, (w, h),
                         flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT,
                         borderValue=0)

    ink = _random_perspective(ink, config.PERSPEKTIVE_MAX)

    scale = random.uniform(config.SKALIERUNG_MIN, config.SKALIERUNG_MAX)
    ink = cv2.resize(
        ink,
        (max(1, int(w * scale)), max(1, int(h * scale))),
        interpolation=cv2.INTER_AREA,
    )

    ink = _stroke_variation(ink)

    return _apply_alpha(ink)


def variant_to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
