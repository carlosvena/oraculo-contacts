import json

import pytest

from oraculo_contacts.exceptions import ImportError
from oraculo_contacts.infrastructure.json_importer import JsonContactImporter


def test_loads_protected_fields_without_modifying_source(tmp_path) -> None:
    source = tmp_path / "contacts.json"
    original = json.dumps(
        {
            "contacts": [
                {
                    "id": "c-1",
                    "display_name": "Ada",
                    "emails": ["ada@example.test"],
                    "favorite": True,
                    "birthday": "1815-12-10",
                    "notes": "protected",
                }
            ]
        }
    )
    source.write_text(original, encoding="utf-8")

    contacts = JsonContactImporter().load(source)

    assert contacts[0].favorite is True
    assert contacts[0].birthday is not None
    assert contacts[0].notes == "protected"
    assert source.read_text(encoding="utf-8") == original


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"contacts": "not-a-list"},
        {"contacts": [{"id": 1}]},
        {"contacts": [{"id": "x", "emails": "not-a-list"}]},
        {"contacts": [{"id": "x", "birthday": "10/12/1815"}]},
    ],
)
def test_rejects_invalid_schema(tmp_path, payload) -> None:
    source = tmp_path / "invalid.json"
    source.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ImportError):
        JsonContactImporter().load(source)


def test_rejects_missing_file(tmp_path) -> None:
    with pytest.raises(ImportError):
        JsonContactImporter().load(tmp_path / "missing.json")


def test_loads_text_in_memory_with_addresses() -> None:
    contacts = JsonContactImporter().load_text(
        '[{"id":"one","display_name":"Ada","addresses":["Calle Demo"]}]'
    )
    assert contacts[0].addresses == ("Calle Demo",)


def test_load_text_reports_invalid_json() -> None:
    with pytest.raises(ImportError, match="archivo cargado"):
        JsonContactImporter().load_text("not-json")
