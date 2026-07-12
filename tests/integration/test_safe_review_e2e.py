import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from oraculo_contacts.application.review_workflow import preview_contacts
from oraculo_contacts.domain.changeset import ChangeDecision, build_changeset
from oraculo_contacts.exceptions import ReportError
from oraculo_contacts.infrastructure.contact_import_service import import_contacts
from oraculo_contacts.infrastructure.safe_export import export_copy

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_csv_review_export_and_reimport_end_to_end(tmp_path) -> None:
    source = FIXTURES / "google_es.csv"
    original = source.read_bytes()
    checksum = hashlib.sha256(original).hexdigest()
    imported = import_contacts(source.name, original.decode("utf-8"))
    changeset = build_changeset(imported.contacts)
    if changeset.changes:
        changeset = changeset.decide(changeset.changes[0].change_id, ChangeDecision.APPROVED)
    if len(changeset.changes) > 1:
        changeset = changeset.decide(changeset.changes[1].change_id, ChangeDecision.REJECTED)
    if len(changeset.changes) > 2:
        changeset = changeset.decide(changeset.changes[2].change_id, ChangeDecision.POSTPONED)
    proposed = preview_contacts(imported.contacts, changeset)
    assert len(proposed) == len(imported.contacts)
    moment = datetime(2026, 7, 12, 15, 30, tzinfo=UTC)
    csv_result = export_copy(
        imported.contacts,
        changeset,
        tmp_path,
        format_="csv",
        source_filename=source.name,
        source_checksum=checksum,
        now=moment,
    )
    vcf_result = export_copy(
        imported.contacts,
        changeset,
        tmp_path,
        format_="vcf",
        source_filename=source.name,
        source_checksum=checksum,
        now=datetime(2026, 7, 12, 15, 31, tzinfo=UTC),
    )
    assert import_contacts(
        csv_result.output.name, csv_result.output.read_text(encoding="utf-8")
    ).contacts
    assert import_contacts(
        vcf_result.output.name, vcf_result.output.read_text(encoding="utf-8")
    ).contacts
    assert source.read_bytes() == original
    manifest = json.loads(csv_result.manifest.read_text(encoding="utf-8"))
    assert manifest["source_checksum"] == checksum
    assert manifest["original_was_modified"] is False
    assert manifest["output_checksum"] == csv_result.output_checksum


def test_json_export_and_overwrite_protection(tmp_path) -> None:
    contacts = import_contacts("contacts.json", '[{"id":"one","display_name":"Ada"}]').contacts
    moment = datetime(2026, 7, 12, 16, 0, tzinfo=UTC)
    result = export_copy(
        contacts,
        build_changeset(contacts),
        tmp_path,
        format_="json",
        source_filename="contacts.json",
        source_checksum="abc",
        now=moment,
    )
    assert (
        json.loads(result.output.read_text(encoding="utf-8"))["contacts"][0]["display_name"]
        == "Ada"
    )
    with pytest.raises(ReportError, match="sobrescribe"):
        export_copy(
            contacts,
            build_changeset(contacts),
            tmp_path,
            format_="json",
            source_filename="contacts.json",
            source_checksum="abc",
            now=moment,
        )
    with pytest.raises(ReportError, match="Formato"):
        export_copy(
            contacts,
            build_changeset(contacts),
            tmp_path,
            format_="pdf",
            source_filename="contacts.json",
            source_checksum="abc",
        )
