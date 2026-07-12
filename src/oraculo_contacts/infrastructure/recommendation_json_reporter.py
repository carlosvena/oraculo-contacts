"""Contrato JSON explícito para planes de acción no ejecutables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from oraculo_contacts.domain.proposals import NormalizationProposal
from oraculo_contacts.domain.recommendations import ActionPlan
from oraculo_contacts.exceptions import ReportError


def action_plan_to_dict(plan: ActionPlan) -> dict[str, Any]:
    """Serializar el plan; los valores protegidos nunca se incluyen."""
    return {
        "schema_version": "3.0",
        "summary": {
            "contacts_analyzed": plan.contacts_analyzed,
            "recommendations": len(plan.recommendations),
            "top_problems": list(plan.top_problems),
            "best_opportunities": list(plan.best_opportunities),
            "estimated_minutes": plan.estimated_minutes,
            "overall_risk": plan.overall_risk.value,
            "explanation": plan.explanation,
            "protected_fields_involved": list(plan.protected_fields_involved),
        },
        "recommendations": [
            {
                "id": item.recommendation_id,
                "contact_refs": list(item.contact_refs),
                "category": item.category,
                "title": item.title,
                "explanation": item.explanation,
                "benefit": item.benefit,
                "risk": item.risk.value,
                "confidence": item.confidence,
                "effort": item.effort.value,
                "estimated_minutes": item.estimated_minutes,
                "priority_score": item.priority_score,
                "proposal": _proposal(item.proposal),
            }
            for item in plan.recommendations
        ],
    }


def _proposal(proposal: NormalizationProposal | None) -> dict[str, Any] | None:
    if proposal is None:
        return None
    return {
        "field": proposal.field,
        "original_value": proposal.original_value,
        "proposed_value": proposal.proposed_value,
        "reason": proposal.reason,
        "confidence": proposal.confidence,
        "risk": proposal.risk.value,
        "rules_applied": list(proposal.rules_applied),
    }


def render_action_plan_json(plan: ActionPlan) -> str:
    """Renderizar un plan JSON legible."""
    return json.dumps(action_plan_to_dict(plan), ensure_ascii=False, indent=2) + "\n"


def write_action_plan(plan: ActionPlan, destination: Path, source: Path) -> None:
    """Escribir un reporte solicitado sin permitir sobrescribir contactos."""
    try:
        if destination.resolve() == source.resolve():
            raise ReportError("La salida no puede sobrescribir el archivo de contactos.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(render_action_plan_json(plan), encoding="utf-8")
    except ReportError:
        raise
    except OSError as error:
        raise ReportError(f"No se pudo escribir el reporte en {destination}: {error}") from error
