"""Entidades inmutables del dominio de contactos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class Contact:
    """Copia inmutable de un contacto importado.

    Los campos ``favorite``, ``birthday`` y ``notes`` son protegidos: las reglas pueden
    comprobar su presencia, pero nunca deben exponer su contenido en reportes.
    """

    source_id: str
    display_name: str
    given_name: str = ""
    family_name: str = ""
    emails: tuple[str, ...] = ()
    phones: tuple[str, ...] = ()
    favorite: bool = False
    birthday: date | None = None
    notes: str | None = None


class Severity(StrEnum):
    """Nivel de severidad de un hallazgo."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class FindingCode(StrEnum):
    """Códigos estables para consumo humano y automático."""

    MISSING_NAME = "missing_name"
    NO_CONTACT_METHOD = "no_contact_method"
    INVALID_EMAIL = "invalid_email"
    INVALID_PHONE = "invalid_phone"
    POSSIBLE_DUPLICATE_EMAIL = "possible_duplicate_email"
    POSSIBLE_DUPLICATE_PHONE = "possible_duplicate_phone"


@dataclass(frozen=True, slots=True)
class Finding:
    """Problema detectado sin incluir valores personales sensibles."""

    code: FindingCode
    severity: Severity
    contact_refs: tuple[str, ...]
    message: str


@dataclass(frozen=True, slots=True)
class AuditReport:
    """Resultado inmutable de una auditoría."""

    contacts_scanned: int
    findings: tuple[Finding, ...]
    generated_at: datetime
    schema_version: str = "1.0"

    @classmethod
    def create(cls, contacts_scanned: int, findings: tuple[Finding, ...]) -> AuditReport:
        """Construir un reporte con marca temporal UTC."""
        return cls(
            contacts_scanned=contacts_scanned,
            findings=findings,
            generated_at=datetime.now(UTC),
        )
