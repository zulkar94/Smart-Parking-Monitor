"""
Automatic Number Plate Recognition for Bangla + English plates.

Pipeline:
  1. detect_plate_regions  -> candidate plate crops (OpenCV contour method;
                               swap for YOLOv8 in production, see README)
  2. read_plate_text       -> EasyOCR reader with ['bn', 'en']
  3. normalize_plate       -> canonical ASCII code used as the DB key, so a
                               Bangla-script read and an English-script read
                               of the same plate resolve to one record.
"""
import re
from functools import lru_cache
from typing import List, Optional

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# 1. Plate localization
# ---------------------------------------------------------------------------

def detect_plate_regions(image: np.ndarray) -> List[np.ndarray]:
    """Return cropped candidate plate regions from a full frame.

    Contour/aspect-ratio heuristic — works for a single reasonably close,
    front-on shot (typical boom-gate camera). For angled/multi-vehicle
    frames, replace this function's body with a YOLOv8 plate-detector
    inference call; keep the same return type (list of BGR crops).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(gray, 30, 200)

    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:15]

    crops = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        aspect = w / float(h) if h else 0
        # Bangladeshi plates are roughly 2:1 to 4.5:1 (single/double line)
        if 1.8 <= aspect <= 5.0 and w > 60 and h > 15:
            crops.append(image[y:y + h, x:x + w])

    if not crops:
        # fall back: treat whole frame as the plate (useful for already-cropped test images)
        crops = [image]
    return crops


# ---------------------------------------------------------------------------
# 2. OCR (Bangla + English)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_reader():
    import easyocr  # imported lazily: slow import + downloads model weights
    return easyocr.Reader(["bn", "en"], gpu=False)


def read_plate_text(plate_crop: np.ndarray) -> Optional[str]:
    """OCR a single plate crop, return the best raw text string (or None)."""
    reader = _get_reader()
    results = reader.readtext(plate_crop, detail=1, paragraph=False)
    if not results:
        return None
    # concatenate all detected text fragments left-to-right, keep highest-confidence line
    results.sort(key=lambda r: r[0][0][0])  # sort by x of top-left corner
    text = " ".join(r[1] for r in results if r[2] > 0.3)
    return text.strip() or None


def recognize_plate(image: np.ndarray) -> Optional[str]:
    """End-to-end: frame -> best raw plate text across all detected regions."""
    best_text, best_len = None, 0
    for crop in detect_plate_regions(image):
        text = read_plate_text(crop)
        if text and len(text) > best_len:
            best_text, best_len = text, len(text)
    return best_text


# ---------------------------------------------------------------------------
# 3. Normalization: Bangla script/digits -> canonical ASCII plate code
# ---------------------------------------------------------------------------

BN_DIGITS = "০১২৩৪৫৬৭৮৯"
EN_DIGITS = "0123456789"
BN_TO_EN_DIGIT = str.maketrans(BN_DIGITS, EN_DIGITS)

# Bangla division/metro name -> transliteration. Extend as needed.
BN_PLACE_MAP = {
    "ঢাকা মেট্রো": "DHAKA-METRO",
    "ঢাকা": "DHAKA",
    "চট্টগ্রাম মেট্রো": "CHATTOGRAM-METRO",
    "চট্টগ্রাম": "CHATTOGRAM",
    "সিলেট মেট্রো": "SYLHET-METRO",
    "রাজশাহী মেট্রো": "RAJSHAHI-METRO",
    "খুলনা মেট্রো": "KHULNA-METRO",
    "বরিশাল মেট্রো": "BARISHAL-METRO",
    "রংপুর মেট্রো": "RANGPUR-METRO",
    "ময়মনসিংহ মেট্রো": "MYMENSINGH-METRO",
}

# Bangla series letters (গ, ঘ, ...) -> Latin transliteration used on English plates
BN_SERIES_MAP = {
    "ক": "KA", "খ": "KHA", "গ": "GA", "ঘ": "GHA", "চ": "CHA", "ছ": "CHHA",
    "জ": "JA", "ঝ": "JHA", "ট": "TA", "ঠ": "THA", "ড": "DA", "ঢ": "DHA",
    "ত": "TA", "থ": "THA", "দ": "DA", "ধ": "DHA", "ন": "NA", "প": "PA",
    "ফ": "PHA", "ব": "BA", "ভ": "BHA", "ম": "MA", "য": "JA", "র": "RA",
    "ল": "LA", "শ": "SHA", "স": "SA", "হ": "HA", "মেট্রো": "METRO",
}


def normalize_plate(raw_text: str) -> str:
    """Turn OCR output (Bangla and/or English, messy spacing/case) into a
    canonical key like 'DHAKA-METRO-GA-11-1234', so the same physical plate
    matches regardless of which script the camera happened to read clearly.
    """
    if not raw_text:
        return ""

    text = raw_text.strip()

    # digits: Bangla -> English
    text = text.translate(BN_TO_EN_DIGIT)

    # known multi-word place names first (longest match wins)
    for bn, en in sorted(BN_PLACE_MAP.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(bn, en)

    # remaining single Bangla series-letter tokens
    for bn, en in BN_SERIES_MAP.items():
        text = re.sub(rf"(?<![A-Za-z]){re.escape(bn)}(?![A-Za-z])", en, text)

    # normalize separators/whitespace, uppercase, collapse to hyphens
    text = text.upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")

    return text


def canonical_plate_from_image(image: np.ndarray) -> Optional[str]:
    """Convenience: image -> canonical plate code, or None if nothing read."""
    raw = recognize_plate(image)
    if not raw:
        return None
    code = normalize_plate(raw)
    return code or None
