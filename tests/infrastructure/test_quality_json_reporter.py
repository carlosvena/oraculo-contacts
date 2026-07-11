import json

import pytest

from oraculo_contacts.domain.models import Contact
from oraculo_contacts.domain.quality_analyzer import analyze_quality
from oraculo_contacts.exceptions import ReportError
from oraculo_contacts.infrastructure.quality_json_reporter import (
    render_quality_json,
    write_quality_json,
)


def test_json_contains_explanations_but_no_protected_values() -> None:
    report = analyze_quality(
        (
            Contact("one", "Ada", emails=("same@example.test",), notes="SECRET"),
            Contact("two", "Ada", emails=("same@example.test",)),
        )
    )
    output = render_quality_json(report)
    payload = json.loads(output)
    assert payload["schema_version"] == "2.0"
    assert payload["duplicate_candidates"][0]["reasons"]
    assert payload["duplicate_candidates"][0]["confidence"] > 0
    assert "SECRET" not in output
    assert "same@example.test" not in output


def test_writer_never_overwrites_source(tmp_path) -> None:
    source = tmp_path / "contacts.json"
    source.write_text("[]", encoding="utf-8")
    with pytest.raises(ReportError):
        write_quality_json(analyze_quality(()), source, source)
    assert source.read_text(encoding="utf-8") == "[]"
