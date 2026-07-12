from datetime import UTC, datetime

import pytest

from oraculo_contacts.domain.changeset import (
    ChangeDecision,
    ChangeSet,
    ProposedChange,
    build_changeset,
)
from oraculo_contacts.domain.models import Contact
from oraculo_contacts.domain.proposals import ProposalRisk


def _protected() -> ProposedChange:
    return ProposedChange(
        "protected",
        "one",
        "protegidos",
        "notes",
        "antes",
        "después",
        datetime.now(UTC),
        "test",
        ("evidence",),
        1.0,
        ProposalRisk.LOW,
        ChangeDecision.BLOCKED,
        "Test",
        "1",
        0,
        True,
    )


def test_bulk_approval_never_approves_protected_fields() -> None:
    normal = ProposedChange(
        "normal",
        "one",
        "nombres",
        "display_name",
        " ada ",
        "Ada",
        datetime.now(UTC),
        "test",
        ("evidence",),
        0.99,
        ProposalRisk.LOW,
        ChangeDecision.PENDING,
        "Test",
        "1",
        20,
    )
    approved = ChangeSet((normal, _protected())).approve_low_risk()
    assert approved.changes[0].decision is ChangeDecision.APPROVED
    assert approved.changes[1].decision is ChangeDecision.BLOCKED


def test_protected_change_requires_individual_explicit_approval() -> None:
    changeset = ChangeSet((_protected(),))
    with pytest.raises(ValueError, match="individual"):
        changeset.decide("protected", ChangeDecision.APPROVED)
    approved = changeset.decide("protected", ChangeDecision.APPROVED, individual_protected=True)
    assert approved.validate()


def test_build_changeset_is_non_destructive_and_summarizes() -> None:
    contact = Contact("one", "  ada  demo ", organization=" Empresa  Demo ")
    snapshot = repr(contact)
    changeset = build_changeset((contact,))
    assert {item.category for item in changeset.changes} >= {"nombres", "organizaciones"}
    assert changeset.summary().pending == len(changeset.changes)
    assert repr(contact) == snapshot
    assert changeset.restore().discard().changes == ()
    with pytest.raises(KeyError):
        changeset.decide("missing", ChangeDecision.REJECTED)


def test_conflicting_approved_changes_are_reported() -> None:
    first = _protected()
    second = ProposedChange(
        "second",
        "one",
        "protegidos",
        "notes",
        "antes",
        "otro",
        datetime.now(UTC),
        "test",
        ("evidence",),
        1.0,
        ProposalRisk.HIGH,
        ChangeDecision.APPROVED,
        "Test",
        "1",
        0,
        True,
    )
    changeset = ChangeSet((first, second)).decide(
        "protected", ChangeDecision.APPROVED, individual_protected=True
    )
    assert changeset.conflicts()[0].field == "notes"
