from pathlib import Path

import pytest

from oraculo_contacts.exceptions import ImportError
from oraculo_contacts.infrastructure.csv_importer import GoogleCsvImporter

FIXTURES = Path(__file__).parents[1] / "fixtures"


@pytest.mark.parametrize("filename", ["google_es.csv", "google_en.csv"])
def test_imports_google_csv_languages_and_preserves_source(filename) -> None:
    source = FIXTURES / filename
    original = source.read_bytes()
    result = GoogleCsvImporter().load_text(original.decode("utf-8"))
    assert result.contacts
    contact = result.contacts[0]
    assert contact.organization
    assert contact.job_title
    assert contact.birthday is not None
    assert contact.notes
    assert contact.labels
    assert source.read_bytes() == original


def test_spanish_csv_supports_multiple_values_and_partial_errors() -> None:
    result = GoogleCsvImporter().load_text((FIXTURES / "google_es.csv").read_text(encoding="utf-8"))
    assert len(result.contacts[0].emails) == 2
    assert len(result.contacts[0].phones) == 2
    assert result.contacts[0].addresses == ("Calle Ficticia 1",)
    assert result.rejected_rows == 1
    assert result.warnings
    assert "Columna desconocida" in result.unknown_fields


def test_csv_ids_are_stable_and_bom_is_supported() -> None:
    content = (FIXTURES / "google_en.csv").read_text(encoding="utf-8")
    importer = GoogleCsvImporter()
    assert (
        importer.load_text(content).contacts[0].source_id
        == importer.load_text("\ufeff" + content).contacts[0].source_id
    )


def test_rejects_empty_csv() -> None:
    with pytest.raises(ImportError, match="vacío"):
        GoogleCsvImporter().load_text("")
