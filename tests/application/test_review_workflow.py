from oraculo_contacts.application.review_workflow import DecisionHistory, preview_contacts
from oraculo_contacts.domain.changeset import ChangeDecision, build_changeset
from oraculo_contacts.domain.models import Contact


def test_preview_applies_only_approved_changes_to_copy() -> None:
    original = Contact("one", "  ada  demo ", notes="protected")
    changeset = build_changeset((original,))
    approved = changeset.decide(changeset.changes[0].change_id, ChangeDecision.APPROVED)
    proposed = preview_contacts((original,), approved)
    assert proposed[0].display_name == "Ada Demo"
    assert original.display_name == "  ada  demo "
    assert proposed[0].notes == "protected"


def test_decision_history_undoes_and_redoes_decisions() -> None:
    changeset = build_changeset((Contact("one", " ada "),))
    updated = changeset.decide(changeset.changes[0].change_id, ChangeDecision.REJECTED)
    history = DecisionHistory((), changeset).record(updated)
    assert history.undo().current == changeset
    assert history.undo().redo().current == updated
    assert DecisionHistory((), changeset).undo().current == changeset
    assert DecisionHistory((), changeset).redo().current == changeset


def test_preview_handles_email_phone_organization_and_address() -> None:
    original = Contact(
        "one",
        "Ada",
        emails=(" ADA@example.test ",),
        phones=("1155550101",),
        addresses=(" Calle  Demo ",),
        organization=" Org  Demo ",
    )
    changeset = build_changeset((original,))
    for change in changeset.changes:
        changeset = changeset.decide(change.change_id, ChangeDecision.APPROVED)
    proposed = preview_contacts((original,), changeset)[0]
    assert proposed.emails != original.emails
    assert proposed.phones != original.phones
    assert proposed.addresses == ("Calle Demo",)
    assert proposed.organization == "Org Demo"
