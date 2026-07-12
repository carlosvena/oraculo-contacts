from dataclasses import FrozenInstanceError

import pytest

from oraculo_contacts.domain.models import Contact
from oraculo_contacts.domain.proposals import ProposalRisk
from oraculo_contacts.domain.recommendations import RecommendationEngine


def test_plan_prioritizes_benefit_confidence_risk_and_effort() -> None:
    contacts = (
        Contact(
            "one",
            "  ada  lovelace ",
            emails=("Ada@EXAMPLE.TEST ",),
            phones=("1155550101",),
            favorite=True,
            notes="SECRET",
        ),
        Contact("two", "Ada Lovelace", emails=("ada@example.test",)),
    )
    snapshot = repr(contacts)
    plan = RecommendationEngine().build_plan(contacts)
    assert plan.contacts_analyzed == 2
    assert plan.recommendations
    assert [item.priority_score for item in plan.recommendations] == sorted(
        [item.priority_score for item in plan.recommendations], reverse=True
    )
    assert plan.estimated_minutes > 0
    assert plan.overall_risk is ProposalRisk.HIGH
    assert plan.protected_fields_involved == ("favorite", "notes")
    assert repr(contacts) == snapshot
    with pytest.raises(FrozenInstanceError):
        plan.explanation = "changed"  # type: ignore[misc]


def test_empty_plan_is_safe_and_non_executable() -> None:
    plan = RecommendationEngine().build_plan(())
    assert plan.recommendations == ()
    assert plan.estimated_minutes == 0
    assert plan.overall_risk is ProposalRisk.LOW
    assert not hasattr(plan, "execute")
    assert not hasattr(plan, "apply")
