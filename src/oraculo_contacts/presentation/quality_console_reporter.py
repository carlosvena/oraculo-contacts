"""Presentación segura del análisis avanzado en consola."""

from __future__ import annotations

from oraculo_contacts.domain.quality_models import QualityReport


def render_quality_console(report: QualityReport) -> str:
    """Mostrar scores, evidencias y prioridades sin datos personales."""
    lines = [
        "ORÁCULO CONTACTS — Análisis de calidad",
        f"Contactos analizados: {report.contacts_analyzed}",
        f"Score general: {report.quality_score}/100",
        f"Posibles duplicados: {len(report.duplicate_candidates)}",
        f"Oportunidades: {len(report.opportunities)}",
    ]
    if report.duplicate_candidates:
        lines.extend(("", "Candidatos a duplicado (requieren revisión humana):"))
        for candidate in report.duplicate_candidates:
            lines.append(
                f"- {', '.join(candidate.contact_refs)} | {candidate.severity.value} | "
                f"confianza {candidate.confidence:.0%}"
            )
            lines.extend(f"  Motivo: {reason}" for reason in candidate.reasons)
            lines.append(f"  Recomendación: {candidate.recommendation}")
    if report.opportunities:
        lines.extend(("", "Prioridades:"))
        for opportunity in report.opportunities:
            lines.append(
                f"{opportunity.priority}. [{opportunity.severity.value}] "
                f"{', '.join(opportunity.contact_refs)} — {opportunity.reason}"
            )
            lines.append(f"   Recomendación: {opportunity.recommendation}")
    return "\n".join(lines) + "\n"
