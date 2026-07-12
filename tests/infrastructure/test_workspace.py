import json

import pytest

from oraculo_contacts.domain.models import Contact
from oraculo_contacts.exceptions import ReportError
from oraculo_contacts.infrastructure.workspace import save_workspace, source_checksum


def test_workspace_requires_outside_path_and_omits_notes(tmp_path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    contact = Contact("one", "Ada", notes="SECRET")
    with pytest.raises(ReportError, match="fuera"):
        save_workspace(
            (contact,), repository / "sessions", source_sha256="abc", repository_root=repository
        )
    output = save_workspace(
        (contact,), tmp_path / "private", source_sha256="abc", repository_root=repository
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["notes_omitted"] is True
    assert "SECRET" not in output.read_text(encoding="utf-8")


def test_checksum_is_deterministic_and_source_is_unchanged(tmp_path) -> None:
    source = tmp_path / "contacts.csv"
    source.write_bytes(b"fictional")
    original = source.read_bytes()
    assert source_checksum(original) == source_checksum(original)
    assert source.read_bytes() == original
