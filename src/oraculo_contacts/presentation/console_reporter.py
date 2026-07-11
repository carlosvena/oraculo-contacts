"""Reporte de auditoría legible para terminales."""

from __future__ import annotations

from oraculo_contacts.domain.models import AuditReport, Severity


def render_console(report: AuditReport) -> str:
    """Renderizar un resumen seguro, sin valores de correo, teléfono ni datos protegidos."""
    counts = {severity: 0 for severity in Severity}
    for finding in report.findings:
        counts[finding.severity] += 1

    lines = [
        "ORÁCULO CONTACTS — Reporte de auditoría",
        f"Contactos analizados: {report.contacts_scanned}",
        f"Hallazgos: {len(report.findings)} "
        f"(errores: {counts[Severity.ERROR]}, advertencias: {counts[Severity.WARNING]}, "
        f"informativos: {counts[Severity.INFO]})",
    ]
    if not report.findings:
        lines.append("No se detectaron problemas con las reglas activas.")
    else:
        lines.append("")
        for finding in report.findings:
            references = ", ".join(finding.contact_refs)
            lines.append(
                f"[{finding.severity.value.upper()}] {finding.code.value} "
                f"({references}): {finding.message}"
            )
    return "\n".join(lines) + "\n"
