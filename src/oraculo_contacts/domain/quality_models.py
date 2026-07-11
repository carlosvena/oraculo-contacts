"""Resultados inmutables del análisis de calidad de contactos."""

from __future__ import annotations

from dataclasses import dataclass

from oraculo_contacts.domain.models import Severity


@dataclass(frozen=True, slots=True)
class QualityIssue:
    """Inconsistencia o carencia explicable de un contacto."""

    code: str
    severity: Severity
    reason: str
    recommendation: str


@dataclass(frozen=True, slots=True)
class ContactQuality:
    """Evaluación de completitud y consistencia de un contacto."""

    contact_ref: str
    score: int
    completeness: int
    issues: tuple[QualityIssue, ...]


@dataclass(frozen=True, slots=True)
class DuplicateCandidate:
    """Par que merece revisión humana, nunca una fusión automática."""

    contact_refs: tuple[str, str]
    matched_on: tuple[str, ...]
    confidence: float
    severity: Severity
    reasons: tuple[str, ...]
    recommendation: str


@dataclass(frozen=True, slots=True)
class ImprovementOpportunity:
    """Acción explicable ordenada por impacto esperado."""

    priority: int
    contact_refs: tuple[str, ...]
    severity: Severity
    reason: str
    recommendation: str


@dataclass(frozen=True, slots=True)
class QualityReport:
    """Resultado agregado del análisis no destructivo."""

    contacts_analyzed: int
    quality_score: int
    contacts: tuple[ContactQuality, ...]
    duplicate_candidates: tuple[DuplicateCandidate, ...]
    opportunities: tuple[ImprovementOpportunity, ...]
