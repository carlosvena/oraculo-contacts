"""Informes de diagnóstico JSON y HTML con enmascarado predeterminado."""

from __future__ import annotations

import html
import json
from datetime import UTC, datetime
from typing import Any

from oraculo_contacts import __version__
from oraculo_contacts.domain.models import Contact
from oraculo_contacts.domain.quality_analyzer import analyze_quality
from oraculo_contacts.domain.recommendations import RecommendationEngine
from oraculo_contacts.infrastructure.import_models import ImportWarning
from oraculo_contacts.ui.view_models import mask_email, mask_phone


def diagnostic_payload(
    contacts: tuple[Contact, ...],
    warnings: tuple[ImportWarning, ...] = (),
    *,
    include_sensitive: bool = False,
) -> dict[str, Any]:
    """Construir un informe explícito sin datos completos salvo consentimiento."""
    quality = analyze_quality(contacts)
    plan = RecommendationEngine().build_plan(contacts)
    return {
        "schema_version": "diagnostic-1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "oraculo_version": __version__,
        "sensitive_data_included": include_sensitive,
        "summary": {
            "contacts": len(contacts),
            "quality_score": quality.quality_score,
            "duplicate_candidates": len(quality.duplicate_candidates),
            "inconsistencies": sum(len(item.issues) for item in quality.contacts),
            "recommendations": len(plan.recommendations),
            "warnings": len(warnings),
        },
        "contacts": [
            {
                "contact_ref": contact.source_id,
                "name": contact.display_name,
                "emails": [
                    value if include_sensitive else mask_email(value) for value in contact.emails
                ],
                "phones": [
                    value if include_sensitive else mask_phone(value) for value in contact.phones
                ],
                "addresses": list(contact.addresses)
                if include_sensitive
                else ["Dirección oculta"] * len(contact.addresses),
                "notes": contact.notes
                if include_sensitive
                else ("Nota protegida" if contact.notes else None),
            }
            for contact in contacts
        ],
        "duplicates": [
            {
                "contact_refs": list(item.contact_refs),
                "confidence": item.confidence,
                "reasons": list(item.reasons),
            }
            for item in quality.duplicate_candidates
        ],
        "inconsistencies": [
            {
                "contact_ref": assessment.contact_ref,
                "issues": [issue.reason for issue in assessment.issues],
            }
            for assessment in quality.contacts
            if assessment.issues
        ],
        "recommendations": [
            {
                "id": item.recommendation_id,
                "title": item.title,
                "explanation": item.explanation,
                "risk": item.risk.value,
                "confidence": item.confidence,
            }
            for item in plan.recommendations
        ],
        "warnings": [
            {"location": item.location, "code": item.code, "message": item.message}
            for item in warnings
        ],
    }


def render_diagnostic_json(payload: dict[str, Any]) -> str:
    """Renderizar informe JSON descargable."""
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_diagnostic_html(payload: dict[str, Any]) -> str:
    """Renderizar un HTML autónomo y seguro mediante escape estricto."""
    summary = payload["summary"]
    contacts = "".join(
        f"<tr><td>{html.escape(str(item['contact_ref']))}</td>"
        f"<td>{html.escape(str(item['name']))}</td>"
        f"<td>{html.escape(', '.join(item['emails']))}</td>"
        f"<td>{html.escape(', '.join(item['phones']))}</td></tr>"
        for item in payload["contacts"]
    )
    sensitive_label = (
        "incluidos por decisión explícita" if payload["sensitive_data_included"] else "enmascarados"
    )
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Informe ORÁCULO CONTACTS</title>
<style>body{{font-family:system-ui;max-width:1100px;margin:40px auto;color:#1f2937}}
table{{border-collapse:collapse;width:100%}}
th,td{{padding:8px;border:1px solid #ddd;text-align:left}}
.safe{{background:#edf8f2;padding:12px;border-radius:8px}}</style></head><body>
<h1>ORÁCULO CONTACTS · Informe de diagnóstico</h1>
<p class="safe">Generado localmente · Versión {html.escape(str(payload["oraculo_version"]))} ·
Datos sensibles: {sensitive_label}</p>
<h2>Resumen</h2><ul><li>Contactos: {summary["contacts"]}</li>
<li>Calidad: {summary["quality_score"]}/100</li>
<li>Duplicados: {summary["duplicate_candidates"]}</li>
<li>Inconsistencias: {summary["inconsistencies"]}</li>
<li>Recomendaciones: {summary["recommendations"]}</li></ul>
<h2>Contactos</h2><table><thead><tr><th>Referencia</th><th>Nombre</th><th>Correos</th><th>Teléfonos</th></tr></thead>
<tbody>{contacts}</tbody></table></body></html>"""
