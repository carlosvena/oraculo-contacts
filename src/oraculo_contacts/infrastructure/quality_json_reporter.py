"""Salida JSON estable para análisis de calidad."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from oraculo_contacts.domain.quality_models import QualityReport
from oraculo_contacts.exceptions import ReportError


def quality_report_to_dict(report: QualityReport) -> dict[str, Any]:
    """Serializar resultados explicables sin valores personales ni campos protegidos."""
    return {
        "schema_version": "2.0",
        "summary": {
            "contacts_analyzed": report.contacts_analyzed,
            "quality_score": report.quality_score,
            "duplicate_candidates": len(report.duplicate_candidates),
            "opportunities": len(report.opportunities),
        },
        "contacts": [
            {
                "contact_ref": item.contact_ref,
                "score": item.score,
                "completeness": item.completeness,
                "issues": [
                    {
                        "code": issue.code,
                        "severity": issue.severity.value,
                        "reason": issue.reason,
                        "recommendation": issue.recommendation,
                    }
                    for issue in item.issues
                ],
            }
            for item in report.contacts
        ],
        "duplicate_candidates": [
            {
                "contact_refs": list(item.contact_refs),
                "matched_on": list(item.matched_on),
                "confidence": item.confidence,
                "severity": item.severity.value,
                "reasons": list(item.reasons),
                "recommendation": item.recommendation,
            }
            for item in report.duplicate_candidates
        ],
        "opportunities": [
            {
                "priority": item.priority,
                "contact_refs": list(item.contact_refs),
                "severity": item.severity.value,
                "reason": item.reason,
                "recommendation": item.recommendation,
            }
            for item in report.opportunities
        ],
    }


def render_quality_json(report: QualityReport) -> str:
    """Renderizar JSON legible."""
    return json.dumps(quality_report_to_dict(report), ensure_ascii=False, indent=2) + "\n"


def write_quality_json(report: QualityReport, destination: Path, source: Path) -> None:
    """Escribir solo el reporte y rechazar cualquier sobrescritura de la fuente."""
    try:
        if destination.resolve() == source.resolve():
            raise ReportError("La salida no puede sobrescribir el archivo de contactos.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(render_quality_json(report), encoding="utf-8")
    except ReportError:
        raise
    except OSError as error:
        raise ReportError(f"No se pudo escribir el reporte en {destination}: {error}") from error
