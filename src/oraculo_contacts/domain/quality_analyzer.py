"""Análisis explicable, determinista y no destructivo de calidad."""

from __future__ import annotations

from collections.abc import Iterable
from difflib import SequenceMatcher
from itertools import combinations

from oraculo_contacts.domain.auditor import audit_contacts
from oraculo_contacts.domain.models import Contact, FindingCode, Severity
from oraculo_contacts.domain.normalization import (
    normalize_email,
    normalize_name,
    normalize_phone,
)
from oraculo_contacts.domain.quality_models import (
    ContactQuality,
    DuplicateCandidate,
    ImprovementOpportunity,
    QualityIssue,
    QualityReport,
)

_SEVERITY_WEIGHT = {Severity.ERROR: 3, Severity.WARNING: 2, Severity.INFO: 1}


def analyze_quality(contacts: tuple[Contact, ...]) -> QualityReport:
    """Analizar una instantánea sin modificar, eliminar ni fusionar contactos."""
    assessments = tuple(_assess_contact(contact) for contact in contacts)
    duplicates = tuple(
        candidate
        for left, right in combinations(contacts, 2)
        if (candidate := _compare_pair(left, right)) is not None
    )
    opportunities = _prioritize(assessments, duplicates)
    score = (
        round(sum(item.score for item in assessments) / len(assessments)) if assessments else 100
    )
    return QualityReport(len(contacts), score, assessments, duplicates, opportunities)


def _assess_contact(contact: Contact) -> ContactQuality:
    """Calcular completitud e inconsistencias con recomendaciones accionables."""
    issues: list[QualityIssue] = []
    has_name = bool(
        contact.display_name.strip() or contact.given_name.strip() or contact.family_name.strip()
    )
    has_method = bool(contact.emails or contact.phones)
    completeness = (
        (35 if has_name else 0)
        + (40 if has_method else 0)
        + (15 if contact.birthday is not None else 0)
        + (10 if contact.notes and contact.notes.strip() else 0)
    )
    if not has_name:
        issues.append(
            _issue(
                "missing_name",
                Severity.WARNING,
                "Falta un nombre utilizable.",
                "Agregar un nombre tras verificar la identidad.",
            )
        )
    if not has_method:
        issues.append(
            _issue(
                "no_contact_method",
                Severity.ERROR,
                "No hay correo ni teléfono.",
                "Agregar una vía de contacto verificada.",
            )
        )
    if contact.display_name.strip() and (contact.given_name.strip() or contact.family_name.strip()):
        components = normalize_name(f"{contact.given_name} {contact.family_name}")
        display = normalize_name(contact.display_name)
        if components and SequenceMatcher(None, display, components).ratio() < 0.55:
            issues.append(
                _issue(
                    "name_mismatch",
                    Severity.WARNING,
                    "El nombre visible difiere de sus componentes.",
                    "Revisar manualmente los campos de nombre.",
                )
            )
    if len({normalize_email(value) for value in contact.emails}) < len(contact.emails):
        issues.append(
            _issue(
                "repeated_email",
                Severity.INFO,
                "El mismo correo aparece repetido en el contacto.",
                "Revisar la repetición sin eliminar datos automáticamente.",
            )
        )
    if len({normalize_phone(value) for value in contact.phones}) < len(contact.phones):
        issues.append(
            _issue(
                "repeated_phone",
                Severity.INFO,
                "El mismo teléfono aparece repetido en el contacto.",
                "Revisar la repetición sin eliminar datos automáticamente.",
            )
        )

    audit_codes = {finding.code for finding in audit_contacts((contact,))}
    if FindingCode.INVALID_EMAIL in audit_codes:
        issues.append(
            _issue(
                "invalid_email",
                Severity.ERROR,
                "Existe un correo con formato inválido.",
                "Verificar el correo con su propietario.",
            )
        )
    if FindingCode.INVALID_PHONE in audit_codes:
        issues.append(
            _issue(
                "invalid_phone",
                Severity.ERROR,
                "Existe un teléfono con formato inválido.",
                "Verificar país, área y número.",
            )
        )
    penalty = sum(
        {Severity.ERROR: 18, Severity.WARNING: 10, Severity.INFO: 4}[item.severity]
        for item in issues
    )
    return ContactQuality(
        contact.source_id, max(0, completeness - penalty), completeness, tuple(issues)
    )


def _issue(code: str, severity: Severity, reason: str, recommendation: str) -> QualityIssue:
    return QualityIssue(code, severity, reason, recommendation)


def _compare_pair(left: Contact, right: Contact) -> DuplicateCandidate | None:
    """Comparar un par y explicar cada señal sin exponer valores personales."""
    matched: list[str] = []
    reasons: list[str] = []
    evidence: list[float] = []
    left_emails = {normalize_email(value) for value in left.emails if value.strip()}
    right_emails = {normalize_email(value) for value in right.emails if value.strip()}
    if left_emails & right_emails:
        matched.append("email")
        reasons.append("Comparten un correo normalizado idéntico.")
        evidence.append(0.98)
    left_phones = {normalize_phone(value) for value in left.phones if normalize_phone(value)}
    right_phones = {normalize_phone(value) for value in right.phones if normalize_phone(value)}
    if left_phones & right_phones:
        matched.append("phone")
        reasons.append("Comparten un teléfono normalizado idéntico.")
        evidence.append(0.96)
    left_name = normalize_name(left.display_name or f"{left.given_name} {left.family_name}")
    right_name = normalize_name(right.display_name or f"{right.given_name} {right.family_name}")
    similarity = (
        SequenceMatcher(None, left_name, right_name).ratio() if left_name and right_name else 0.0
    )
    if similarity >= 0.82:
        matched.append("name")
        reasons.append(f"Los nombres tienen {similarity:.0%} de similitud normalizada.")
        evidence.append(0.72 + similarity * 0.2)
    if not evidence or (matched == ["name"] and similarity < 0.9):
        return None
    confidence = round(1 - _product(1 - value for value in evidence), 2)
    severity = Severity.ERROR if confidence >= 0.97 else Severity.WARNING
    return DuplicateCandidate(
        (left.source_id, right.source_id),
        tuple(matched),
        confidence,
        severity,
        tuple(reasons),
        "Revisar ambos contactos manualmente; no fusionar ni eliminar automáticamente.",
    )


def _product(values: Iterable[float]) -> float:
    result = 1.0
    for value in values:
        result *= value
    return result


def _prioritize(
    assessments: tuple[ContactQuality, ...], duplicates: tuple[DuplicateCandidate, ...]
) -> tuple[ImprovementOpportunity, ...]:
    candidates: list[tuple[int, tuple[str, ...], Severity, str, str]] = []
    for assessment in assessments:
        for issue in assessment.issues:
            candidates.append(
                (
                    _SEVERITY_WEIGHT[issue.severity],
                    (assessment.contact_ref,),
                    issue.severity,
                    issue.reason,
                    issue.recommendation,
                )
            )
    for duplicate in duplicates:
        candidates.append(
            (
                _SEVERITY_WEIGHT[duplicate.severity],
                duplicate.contact_refs,
                duplicate.severity,
                "Posible duplicado con evidencia explicada.",
                duplicate.recommendation,
            )
        )
    candidates.sort(key=lambda item: (-item[0], item[1], item[3]))
    return tuple(
        ImprovementOpportunity(index, refs, severity, reason, recommendation)
        for index, (_, refs, severity, reason, recommendation) in enumerate(candidates, 1)
    )
