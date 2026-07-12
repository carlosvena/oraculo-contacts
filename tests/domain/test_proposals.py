from dataclasses import FrozenInstanceError

import pytest

from oraculo_contacts.domain.models import Contact
from oraculo_contacts.domain.normalization import PhoneKind
from oraculo_contacts.domain.proposals import propose_contact_normalizations


def test_proposes_name_and_email_without_mutating_contact() -> None:
    contact = Contact(
        "one",
        "  jOSÉ   péREZ ",
        emails=(" User@EXAMPLE.TEST ",),
        favorite=True,
        notes="protected",
    )
    snapshot = repr(contact)
    proposals = propose_contact_normalizations(contact)
    assert [item.field for item in proposals] == ["display_name", "email"]
    assert proposals[0].original_value == "  jOSÉ   péREZ "
    assert proposals[0].proposed_value == "José Pérez"
    assert proposals[1].proposed_value == "User@example.test"
    assert all(item.reason and item.rules_applied for item in proposals)
    assert repr(contact) == snapshot
    assert contact.favorite is True
    assert contact.notes == "protected"
    with pytest.raises(FrozenInstanceError):
        proposals[0].reason = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("number", "kind", "expected"),
    [
        ("08005550101", PhoneKind.TOLL_FREE, "0800 555-0101"),
        ("08105550101", PhoneKind.TOLL_FREE, "0810 555-0101"),
        ("1155550101", PhoneKind.LANDLINE, "+54 11 5555-0101"),
        ("+5491155550101", PhoneKind.MOBILE, "+54 9 11 5555-0101"),
    ],
)
def test_argentine_phone_proposals_preserve_conservative_kind(number, kind, expected) -> None:
    proposal = propose_contact_normalizations(Contact("one", "Ada", phones=(number,)))[0]
    assert proposal.phone_kind is kind
    assert (
        proposal.phone_kind is PhoneKind.MOBILE
        if kind is PhoneKind.MOBILE
        else proposal.phone_kind is not PhoneKind.MOBILE
    )
    assert proposal.proposed_value == expected


def test_does_not_propose_invalid_email_or_unknown_phone() -> None:
    contact = Contact("one", "Ada", emails=("invalid email",), phones=("12",))
    assert propose_contact_normalizations(contact) == ()
