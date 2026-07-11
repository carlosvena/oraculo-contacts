"""Propuestas inmutables de normalización que nunca modifican contactos."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum

from oraculo_contacts.domain.models import Contact
from oraculo_contacts.domain.normalization import PhoneKind, classify_phone, normalize_phone


class ProposalRisk(StrEnum):
    """Riesgo de que una propuesta requiera interpretación humana."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class NormalizationProposal:
    """Cambio sugerido y reversible sobre un único valor no protegido."""

    contact_ref: str
    field: str
    original_value: str
    proposed_value: str
    reason: str
    confidence: float
    risk: ProposalRisk
    rules_applied: tuple[str, ...]
    phone_kind: PhoneKind | None = None


def propose_contact_normalizations(contact: Contact) -> tuple[NormalizationProposal, ...]:
    """Crear propuestas sin mutar el contacto ni inspeccionar valores protegidos."""
    proposals: list[NormalizationProposal] = []
    name = _propose_name(contact.source_id, contact.display_name)
    if name is not None:
        proposals.append(name)
    proposals.extend(
        proposal
        for value in contact.emails
        if (proposal := _propose_email(contact.source_id, value)) is not None
    )
    proposals.extend(
        proposal
        for value in contact.phones
        if (proposal := _propose_argentine_phone(contact.source_id, value)) is not None
    )
    return tuple(proposals)


def _propose_name(contact_ref: str, value: str) -> NormalizationProposal | None:
    """Proponer espacios y capitalización conservadora para un nombre."""
    collapsed = " ".join(value.split())
    proposed = " ".join(_title_name_part(part) for part in collapsed.split(" "))
    if not proposed or proposed == value:
        return None
    return NormalizationProposal(
        contact_ref,
        "display_name",
        value,
        proposed,
        "El nombre contiene espacios irregulares o capitalización inconsistente.",
        0.93,
        ProposalRisk.LOW,
        ("collapse_whitespace", "conservative_name_case"),
    )


def _title_name_part(part: str) -> str:
    lowered = part.casefold()
    if lowered in {"de", "del", "la", "las", "los", "y"}:
        return lowered
    return "-".join(segment[:1].upper() + segment[1:].lower() for segment in part.split("-"))


def _propose_email(contact_ref: str, value: str) -> NormalizationProposal | None:
    """Proponer una forma canónica solo cuando la sintaxis básica es segura."""
    proposed = unicodedata.normalize("NFKC", value).strip()
    if proposed.count("@") != 1 or any(character.isspace() for character in proposed):
        return None
    local, domain = proposed.split("@")
    proposed = f"{local}@{domain.casefold()}"
    if not local or "." not in domain or proposed == value:
        return None
    return NormalizationProposal(
        contact_ref,
        "email",
        value,
        proposed,
        "El correo puede representarse sin espacios exteriores y con dominio en minúsculas.",
        0.99,
        ProposalRisk.LOW,
        ("unicode_nfkc", "trim_outer_whitespace", "lowercase_domain"),
    )


def _propose_argentine_phone(contact_ref: str, value: str) -> NormalizationProposal | None:
    """Proponer formato legible argentino sin inventar tipo ni dígitos."""
    kind = classify_phone(value)
    digits = normalize_phone(value)
    if not digits:
        return None
    proposed: str | None = None
    rules: tuple[str, ...] = ()
    confidence = 0.9
    risk = ProposalRisk.LOW
    if kind is PhoneKind.TOLL_FREE and len(digits) == 11:
        proposed = f"{digits[:4]} {digits[4:7]}-{digits[7:]}"
        rules = ("argentina_service_prefix", "group_digits")
    elif kind is PhoneKind.MOBILE and len(digits) == 11 and digits.startswith("9"):
        proposed = f"+54 9 {digits[1:3]} {digits[3:7]}-{digits[7:]}"
        rules = ("argentina_country_code", "explicit_mobile_marker", "group_digits")
    elif kind is PhoneKind.LANDLINE and len(digits) == 10:
        proposed = f"+54 {digits[:2]} {digits[2:6]}-{digits[6:]}"
        rules = ("argentina_country_code", "preserve_landline_kind", "group_digits")
        confidence = 0.82
        risk = ProposalRisk.MEDIUM
    if proposed is None or _phone_equivalent_format(value, proposed):
        return None
    return NormalizationProposal(
        contact_ref,
        "phone",
        value,
        proposed,
        f"El teléfono argentino puede formatearse preservando su clasificación {kind.value}.",
        confidence,
        risk,
        rules,
        kind,
    )


def _phone_equivalent_format(original: str, proposed: str) -> bool:
    return re.sub(r"\s+", " ", original.strip()) == proposed
