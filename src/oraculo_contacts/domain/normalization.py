"""Normalización efímera utilizada exclusivamente para comparar."""

from __future__ import annotations

import re
import unicodedata
from enum import StrEnum


class PhoneKind(StrEnum):
    """Clasificación conservadora de teléfonos argentinos."""

    MOBILE = "mobile"
    TOLL_FREE = "toll_free"
    LANDLINE = "landline"
    UNKNOWN = "unknown"


def normalize_name(value: str) -> str:
    """Normalizar un nombre en memoria para similitud; no altera la entidad."""
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    ascii_text = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(re.findall(r"[a-z0-9]+", ascii_text))


def normalize_email(value: str) -> str:
    """Normalizar espacios y capitalización para comparación exacta."""
    return value.strip().casefold()


def normalize_phone(value: str) -> str:
    """Conservar solo dígitos y retirar prefijos de llamada internacionales comunes."""
    digits = "".join(character for character in value if character.isdigit())
    if digits.startswith("0054"):
        digits = digits[4:]
    elif digits.startswith("54") and len(digits) > 10:
        digits = digits[2:]
    return digits


def classify_phone(value: str) -> PhoneKind:
    """Clasificar sin asumir que líneas 0800, 0810 o fijas son celulares."""
    digits = normalize_phone(value)
    national = digits[1:] if digits.startswith("0") and len(digits) > 10 else digits
    if national.startswith(("800", "810")):
        return PhoneKind.TOLL_FREE
    if national.startswith("9") and len(national) in {11, 12}:
        return PhoneKind.MOBILE
    if len(national) in {8, 9, 10, 11}:
        return PhoneKind.LANDLINE
    return PhoneKind.UNKNOWN
