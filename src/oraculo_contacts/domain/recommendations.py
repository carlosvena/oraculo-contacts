"""Motor determinista de recomendaciones que produce planes, nunca acciones."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from oraculo_contacts.domain.models import Contact, Severity
from oraculo_contacts.domain.proposals import (
    NormalizationProposal,
    ProposalRisk,
    propose_contact_normalizations,
)
from oraculo_contacts.domain.quality_analyzer import analyze_quality


class Effort(StrEnum):
    """Esfuerzo humano estimado para revisar una recomendación."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class Recommendation:
    """Oportunidad explicable que no posee capacidad de ejecución."""

    recommendation_id: str
    contact_refs: tuple[str, ...]
    category: str
    title: str
    explanation: str
    benefit: int
    risk: ProposalRisk
    confidence: float
    effort: Effort
    estimated_minutes: int
    priority_score: float
    proposal: NormalizationProposal | None = None


@dataclass(frozen=True, slots=True)
class ActionPlan:
    """Plan ordenado para revisión humana, sin métodos de aplicación."""

    contacts_analyzed: int
    recommendations: tuple[Recommendation, ...]
    top_problems: tuple[str, ...]
    best_opportunities: tuple[str, ...]
    estimated_minutes: int
    overall_risk: ProposalRisk
    explanation: str
    protected_fields_involved: tuple[str, ...]


class RecommendationEngine:
    """Combinar calidad y propuestas existentes sin duplicar sus reglas."""

    def build_plan(self, contacts: tuple[Contact, ...]) -> ActionPlan:
        """Construir un plan determinista a partir de una instantánea inmutable."""
        quality = analyze_quality(contacts)
        recommendations: list[Recommendation] = []
        for contact in contacts:
            for proposal in propose_contact_normalizations(contact):
                recommendations.append(self._from_proposal(proposal, len(recommendations) + 1))
        for opportunity in quality.opportunities:
            recommendations.append(
                self._from_quality(
                    opportunity.contact_refs,
                    opportunity.reason,
                    opportunity.recommendation,
                    opportunity.severity,
                    len(recommendations) + 1,
                )
            )
        recommendations.sort(key=lambda item: (-item.priority_score, item.recommendation_id))
        protected = self._protected_fields_present(contacts)
        problems = tuple(dict.fromkeys(item.reason for item in quality.opportunities))[:5]
        best = tuple(item.title for item in recommendations[:5])
        total_minutes = sum(item.estimated_minutes for item in recommendations)
        risk = max(
            (item.risk for item in recommendations), key=_risk_weight, default=ProposalRisk.LOW
        )
        return ActionPlan(
            len(contacts),
            tuple(recommendations),
            problems,
            best,
            total_minutes,
            risk,
            "Prioridad calculada con beneficio, confianza, riesgo y esfuerzo; nada se ejecuta.",
            protected,
        )

    @staticmethod
    def _from_proposal(proposal: NormalizationProposal, sequence: int) -> Recommendation:
        benefit = 55 if proposal.field == "phone" else 40
        effort = Effort.LOW
        minutes = 2
        score = _priority(benefit, proposal.confidence, proposal.risk, effort)
        return Recommendation(
            f"normalization-{sequence}",
            (proposal.contact_ref,),
            "normalization",
            f"Revisar normalización de {proposal.field}",
            proposal.reason,
            benefit,
            proposal.risk,
            proposal.confidence,
            effort,
            minutes,
            score,
            proposal,
        )

    @staticmethod
    def _from_quality(
        refs: tuple[str, ...],
        reason: str,
        recommendation: str,
        severity: Severity,
        sequence: int,
    ) -> Recommendation:
        benefit = {Severity.ERROR: 90, Severity.WARNING: 65, Severity.INFO: 35}[severity]
        risk = ProposalRisk.HIGH if len(refs) > 1 else ProposalRisk.MEDIUM
        confidence = {Severity.ERROR: 0.95, Severity.WARNING: 0.85, Severity.INFO: 0.75}[severity]
        effort = Effort.HIGH if len(refs) > 1 else Effort.MEDIUM
        minutes = 8 if effort is Effort.HIGH else 5
        return Recommendation(
            f"quality-{sequence}",
            refs,
            "quality",
            recommendation,
            reason,
            benefit,
            risk,
            confidence,
            effort,
            minutes,
            _priority(benefit, confidence, risk, effort),
        )

    @staticmethod
    def _protected_fields_present(contacts: tuple[Contact, ...]) -> tuple[str, ...]:
        fields: list[str] = []
        if any(contact.favorite for contact in contacts):
            fields.append("favorite")
        if any(contact.birthday is not None for contact in contacts):
            fields.append("birthday")
        if any(contact.notes is not None for contact in contacts):
            fields.append("notes")
        return tuple(fields)


def _priority(benefit: int, confidence: float, risk: ProposalRisk, effort: Effort) -> float:
    """Ponderar beneficio y evidencia contra riesgo y esfuerzo."""
    risk_penalty = {ProposalRisk.LOW: 1.0, ProposalRisk.MEDIUM: 0.75, ProposalRisk.HIGH: 0.5}[risk]
    effort_penalty = {Effort.LOW: 1.0, Effort.MEDIUM: 0.8, Effort.HIGH: 0.6}[effort]
    return round(benefit * confidence * risk_penalty * effort_penalty, 2)


def _risk_weight(risk: ProposalRisk) -> int:
    return {ProposalRisk.LOW: 1, ProposalRisk.MEDIUM: 2, ProposalRisk.HIGH: 3}[risk]
