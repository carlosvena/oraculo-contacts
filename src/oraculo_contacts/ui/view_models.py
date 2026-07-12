"""Funciones puras que preparan datos seguros para la interfaz visual."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from oraculo_contacts.domain.models import Contact
from oraculo_contacts.domain.quality_analyzer import analyze_quality


class PresenceFilter(StrEnum):
    """Filtro ternario para campos opcionales."""

    ALL = "Todos"
    WITH = "Con"
    WITHOUT = "Sin"


class QualityLevel(StrEnum):
    """Tramos visibles del score de calidad."""

    ALL = "Todos"
    HIGH = "Alta (80-100)"
    MEDIUM = "Media (50-79)"
    LOW = "Baja (0-49)"


@dataclass(frozen=True, slots=True)
class DashboardMetrics:
    """Métricas agregadas calculadas sin exponer valores personales."""

    contacts: int
    favorites: int
    birthdays: int
    with_notes: int
    phones: int
    emails: int
    addresses: int
    quality_score: int
    duplicate_candidates: int
    inconsistencies: int
    opportunities: int


def dashboard_metrics(contacts: tuple[Contact, ...]) -> DashboardMetrics:
    """Calcular métricas mediante el motor de calidad existente."""
    quality = analyze_quality(contacts)
    return DashboardMetrics(
        contacts=len(contacts),
        favorites=sum(contact.favorite for contact in contacts),
        birthdays=sum(contact.birthday is not None for contact in contacts),
        with_notes=sum(bool(contact.notes) for contact in contacts),
        phones=sum(len(contact.phones) for contact in contacts),
        emails=sum(len(contact.emails) for contact in contacts),
        addresses=sum(len(contact.addresses) for contact in contacts),
        quality_score=quality.quality_score,
        duplicate_candidates=len(quality.duplicate_candidates),
        inconsistencies=sum(len(item.issues) for item in quality.contacts),
        opportunities=len(quality.opportunities),
    )


def mask_email(value: str) -> str:
    """Ocultar parcialmente un correo para vistas generales."""
    if "@" not in value:
        return "••••"
    local, domain = value.split("@", 1)
    visible = local[:1] if local else ""
    return f"{visible}•••@{domain}"


def mask_phone(value: str) -> str:
    """Ocultar todos salvo los últimos cuatro dígitos."""
    digits = "".join(character for character in value if character.isdigit())
    return f"•••• {digits[-4:]}" if len(digits) >= 4 else "••••"


def filter_contacts(
    contacts: tuple[Contact, ...],
    *,
    query: str = "",
    favorite: PresenceFilter = PresenceFilter.ALL,
    birthday: PresenceFilter = PresenceFilter.ALL,
    phone: PresenceFilter = PresenceFilter.ALL,
    email: PresenceFilter = PresenceFilter.ALL,
    quality: QualityLevel = QualityLevel.ALL,
) -> tuple[Contact, ...]:
    """Filtrar contactos sin alterar el orden ni los objetos originales."""
    scores = {item.contact_ref: item.score for item in analyze_quality(contacts).contacts}
    normalized_query = query.strip().casefold()
    return tuple(
        contact
        for contact in contacts
        if (not normalized_query or normalized_query in _name(contact).casefold())
        and _presence(contact.favorite, favorite)
        and _presence(contact.birthday is not None, birthday)
        and _presence(bool(contact.phones), phone)
        and _presence(bool(contact.emails), email)
        and _quality_matches(scores[contact.source_id], quality)
    )


def contact_summary(contact: Contact, score: int) -> dict[str, str | int]:
    """Preparar una fila navegable con correo y teléfono enmascarados."""
    return {
        "Referencia": contact.source_id,
        "Nombre": _name(contact) or "Sin nombre",
        "Teléfono": mask_phone(contact.phones[0]) if contact.phones else "—",
        "Correo": mask_email(contact.emails[0]) if contact.emails else "—",
        "Calidad": score,
    }


def _name(contact: Contact) -> str:
    return contact.display_name or f"{contact.given_name} {contact.family_name}".strip()


def _presence(value: bool, selected: PresenceFilter) -> bool:
    return selected is PresenceFilter.ALL or value is (selected is PresenceFilter.WITH)


def _quality_matches(score: int, level: QualityLevel) -> bool:
    return (
        level is QualityLevel.ALL
        or (level is QualityLevel.HIGH and score >= 80)
        or (level is QualityLevel.MEDIUM and 50 <= score < 80)
        or (level is QualityLevel.LOW and score < 50)
    )
