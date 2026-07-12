from pathlib import Path

import pytest

from oraculo_contacts.exceptions import ImportError
from oraculo_contacts.infrastructure.contact_import_service import detect_format, import_contacts
from oraculo_contacts.infrastructure.import_models import ContactFormat

FIXTURES = Path(__file__).parents[1] / "fixtures"


@pytest.mark.parametrize(
    ("name", "content", "expected"),
    [
        ("contacts.json", "[]", ContactFormat.JSON),
        ("contacts.csv", "Name,Phone 1 - Value\nAda,123", ContactFormat.GOOGLE_CSV),
        ("contacts.vcf", "BEGIN:VCARD\nEND:VCARD", ContactFormat.VCARD),
        ("unknown", "BEGIN:VCARD\nEND:VCARD", ContactFormat.VCARD),
    ],
)
def test_detects_format(name, content, expected) -> None:
    assert detect_format(name, content) is expected


def test_import_facade_supports_all_formats() -> None:
    assert import_contacts("contacts.json", "[]").format is ContactFormat.JSON
    csv_content = (FIXTURES / "google_en.csv").read_text(encoding="utf-8")
    assert import_contacts("contacts.csv", csv_content).contacts
    vcf_content = (FIXTURES / "contact_v3.vcf").read_text(encoding="utf-8")
    assert import_contacts("contacts.vcf", vcf_content).contacts


def test_unknown_format_is_clear() -> None:
    with pytest.raises(ImportError, match="detectar"):
        detect_format("contacts.bin", "opaque")
