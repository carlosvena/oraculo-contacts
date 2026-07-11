import json

import pytest

from oraculo_contacts.domain.models import Contact
from oraculo_contacts.domain.recommendations import RecommendationEngine
from oraculo_contacts.exceptions import ReportError
from oraculo_contacts.infrastructure.recommendation_json_reporter import (
    render_action_plan_json,
    write_action_plan,
)


def test_json_contract_contains_explanations_and_not_protected_values() -> None:
    plan = RecommendationEngine().build_plan(
        (Contact("one", "  ada ", favorite=True, notes="SECRET"),)
    )
    output = render_action_plan_json(plan)
    payload = json.loads(output)
    assert payload["schema_version"] == "3.0"
    assert payload["summary"]["protected_fields_involved"] == ["favorite", "notes"]
    proposal = next(item["proposal"] for item in payload["recommendations"] if item["proposal"])
    assert proposal["original_value"] == "  ada "
    assert payload["recommendations"][0]["explanation"]
    assert "SECRET" not in output


def test_writer_refuses_to_overwrite_source(tmp_path) -> None:
    source = tmp_path / "contacts.json"
    source.write_text("[]", encoding="utf-8")
    with pytest.raises(ReportError, match="sobrescribir"):
        write_action_plan(RecommendationEngine().build_plan(()), source, source)
    assert source.read_text(encoding="utf-8") == "[]"
