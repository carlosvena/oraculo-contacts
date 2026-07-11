from pathlib import Path

from oraculo_contacts.application.use_cases import AuditContacts
from oraculo_contacts.domain.models import Contact, FindingCode


class StubImporter:
    def load(self, source: Path) -> tuple[Contact, ...]:
        assert source == Path("contacts.json")
        return (Contact("one", "One"),)


def test_audit_contacts_orchestrates_import_and_rules() -> None:
    report = AuditContacts(StubImporter()).execute(Path("contacts.json"))
    assert report.contacts_scanned == 1
    assert report.findings[0].code is FindingCode.NO_CONTACT_METHOD
