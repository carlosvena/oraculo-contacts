from oraculo_contacts.domain.auditor import audit_contacts
from oraculo_contacts.domain.models import Contact, FindingCode


def test_reports_quality_issues_without_changing_contact() -> None:
    contact = Contact(
        source_id="c-1",
        display_name="",
        emails=("invalid",),
        phones=("12",),
        favorite=True,
        notes="never expose me",
    )

    findings = audit_contacts((contact,))

    assert {finding.code for finding in findings} == {
        FindingCode.MISSING_NAME,
        FindingCode.INVALID_EMAIL,
        FindingCode.INVALID_PHONE,
    }
    assert contact.favorite is True
    assert contact.notes == "never expose me"
    assert all("never expose me" not in finding.message for finding in findings)


def test_detects_duplicates_without_proposing_a_merge() -> None:
    contacts = (
        Contact("one", "One", emails=("Same@Example.test",), phones=("+54 11 5555-0000",)),
        Contact("two", "Two", emails=("same@example.test",), phones=("541155550000",)),
    )

    findings = audit_contacts(contacts)

    duplicates = [
        finding
        for finding in findings
        if finding.code
        in {FindingCode.POSSIBLE_DUPLICATE_EMAIL, FindingCode.POSSIBLE_DUPLICATE_PHONE}
    ]
    assert len(duplicates) == 2
    assert all(finding.contact_refs == ("one", "two") for finding in duplicates)
    assert all("fusion" not in finding.message.casefold() for finding in duplicates)


def test_reports_contact_without_contact_method() -> None:
    findings = audit_contacts((Contact("one", "One"),))
    assert [finding.code for finding in findings] == [FindingCode.NO_CONTACT_METHOD]
