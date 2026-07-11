"""Serialización segura de reportes de auditoría."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from oraculo_contacts.domain.models import AuditReport
from oraculo_contacts.exceptions import ReportError


def report_to_dict(report: AuditReport) -> dict[str, Any]:
    """Convertir un reporte a un contrato JSON estable y sin datos protegidos."""
    counts = {"info": 0, "warning": 0, "error": 0}
    for finding in report.findings:
        counts[finding.severity.value] += 1
    return {
        "schema_version": report.schema_version,
        "generated_at": report.generated_at.isoformat(),
        "summary": {
            "contacts_scanned": report.contacts_scanned,
            "findings": len(report.findings),
            "by_severity": counts,
        },
        "findings": [
            {
                "code": finding.code.value,
                "severity": finding.severity.value,
                "contact_refs": list(finding.contact_refs),
                "message": finding.message,
            }
            for finding in report.findings
        ],
    }


def render_json(report: AuditReport) -> str:
    """Renderizar un reporte JSON legible y determinista."""
    return json.dumps(report_to_dict(report), ensure_ascii=False, indent=2) + "\n"


def write_json_report(report: AuditReport, destination: Path, source: Path) -> None:
    """Escribir un reporte nuevo, rechazando siempre la ruta del origen."""
    try:
        if destination.resolve() == source.resolve():
            raise ReportError("La salida no puede sobrescribir el archivo de contactos.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(render_json(report), encoding="utf-8")
    except ReportError:
        raise
    except OSError as error:
        raise ReportError(f"No se pudo escribir el reporte en {destination}: {error}") from error
