"""Reglas puras de auditoría de contactos."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable

from oraculo_contacts.domain.models import Contact, Finding, FindingCode, Severity

_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_PHONE_ALLOWED = re.compile(r"^\+?[0-9().\s-]+$")


def audit_contacts(contacts: Iterable[Contact]) -> tuple[Finding, ...]:
    """Evaluar contactos sin mutarlos y devolver hallazgos deterministas."""
    items = tuple(contacts)
    findings: list[Finding] = []
    emails: dict[str, list[str]] = defaultdict(list)
    phones: dict[str, list[str]] = defaultdict(list)

    for contact in items:
        ref = (contact.source_id,)
        if not contact.display_name.strip() and not (
            contact.given_name.strip() or contact.family_name.strip()
        ):
            findings.append(
                Finding(
                    FindingCode.MISSING_NAME, Severity.WARNING, ref, "El contacto no tiene nombre."
                )
            )
        if not contact.emails and not contact.phones:
            findings.append(
                Finding(
                    FindingCode.NO_CONTACT_METHOD,
                    Severity.WARNING,
                    ref,
                    "El contacto no tiene correo ni teléfono.",
                )
            )
        for email in contact.emails:
            normalized = email.strip().casefold()
            if not _EMAIL.fullmatch(normalized):
                findings.append(
                    Finding(
                        FindingCode.INVALID_EMAIL,
                        Severity.ERROR,
                        ref,
                        "El contacto contiene un correo con formato inválido.",
                    )
                )
            elif contact.source_id not in emails[normalized]:
                emails[normalized].append(contact.source_id)
        for phone in contact.phones:
            digits = "".join(character for character in phone if character.isdigit())
            if not _PHONE_ALLOWED.fullmatch(phone.strip()) or not 7 <= len(digits) <= 15:
                findings.append(
                    Finding(
                        FindingCode.INVALID_PHONE,
                        Severity.ERROR,
                        ref,
                        "El contacto contiene un teléfono con formato inválido.",
                    )
                )
            elif contact.source_id not in phones[digits]:
                phones[digits].append(contact.source_id)

    findings.extend(_duplicate_findings(emails, FindingCode.POSSIBLE_DUPLICATE_EMAIL, "correo"))
    findings.extend(_duplicate_findings(phones, FindingCode.POSSIBLE_DUPLICATE_PHONE, "teléfono"))
    return tuple(findings)


def _duplicate_findings(
    index: dict[str, list[str]], code: FindingCode, label: str
) -> list[Finding]:
    """Crear advertencias agrupadas sin revelar el valor coincidente."""
    return [
        Finding(
            code,
            Severity.WARNING,
            tuple(references),
            f"Posible duplicado: {len(references)} contactos comparten un {label}.",
        )
        for references in index.values()
        if len(references) > 1
    ]
