from pathlib import Path

import pytest

from oraculo_contacts.exceptions import ImportError
from oraculo_contacts.infrastructure.vcard_importer import VCardImporter

FIXTURES = Path(__file__).parents[1] / "fixtures"


@pytest.mark.parametrize("filename", ["contact_v3.vcf", "contact_v4.vcard"])
def test_imports_vcard_versions_and_preserves_known_fields(filename) -> None:
    source = FIXTURES / filename
    original = source.read_bytes()
    result = VCardImporter().load_text(original.decode("utf-8"))
    contact = result.contacts[0]
    assert contact.display_name
    assert contact.phones
    assert contact.emails
    assert contact.addresses
    assert contact.organization
    assert contact.job_title
    assert contact.birthday is not None
    assert contact.notes
    assert contact.labels
    assert source.read_bytes() == original


def test_vcard_warns_about_unknown_fields_without_losing_contact() -> None:
    result = VCardImporter().load_text((FIXTURES / "contact_v3.vcf").read_text(encoding="utf-8"))
    assert len(result.contacts) == 1
    assert "X-CUSTOM" in result.unknown_fields


def test_rejects_empty_or_unstructured_vcard() -> None:
    with pytest.raises(ImportError, match="vacío"):
        VCardImporter().load_text("")
    with pytest.raises(ImportError, match="BEGIN:VCARD"):
        VCardImporter().load_text("FN:No block")
