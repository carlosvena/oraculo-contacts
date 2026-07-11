import json

import pytest

from oraculo_contacts.domain.models import AuditReport, Finding, FindingCode, Severity
from oraculo_contacts.exceptions import ReportError
from oraculo_contacts.infrastructure.json_reporter import render_json, write_json_report


def _report() -> AuditReport:
    return AuditReport.create(
        1,
        (
            Finding(
                FindingCode.MISSING_NAME,
                Severity.WARNING,
                ("c-1",),
                "El contacto no tiene nombre.",
            ),
        ),
    )


def test_renders_stable_json_contract() -> None:
    payload = json.loads(render_json(_report()))
    assert payload["schema_version"] == "1.0"
    assert payload["summary"]["contacts_scanned"] == 1
    assert payload["summary"]["by_severity"]["warning"] == 1
    assert payload["findings"][0]["contact_refs"] == ["c-1"]


def test_never_overwrites_source(tmp_path) -> None:
    source = tmp_path / "contacts.json"
    source.write_text("[]", encoding="utf-8")

    with pytest.raises(ReportError, match="sobrescribir"):
        write_json_report(_report(), source, source)

    assert source.read_text(encoding="utf-8") == "[]"
