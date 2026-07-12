"""Contratos inmutables para importaciones tolerantes y explicables."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from oraculo_contacts.domain.models import Contact


class ContactFormat(StrEnum):
    """Formatos de contacto admitidos localmente."""

    JSON = "json"
    GOOGLE_CSV = "csv"
    VCARD = "vcf"


@dataclass(frozen=True, slots=True)
class ImportWarning:
    """Advertencia segura que no contiene datos personales."""

    location: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ImportResult:
    """Resultado de importación parcial mantenido únicamente en memoria."""

    format: ContactFormat
    contacts: tuple[Contact, ...]
    warnings: tuple[ImportWarning, ...]
    rejected_rows: int
    recognized_fields: tuple[str, ...]
    unknown_fields: tuple[str, ...]

    @property
    def contacts_with_warnings(self) -> int:
        """Contar ubicaciones únicas con advertencias."""
        return len({warning.location for warning in self.warnings})
