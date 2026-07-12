"""Exportación de copias nuevas en JSON, Google CSV y vCard."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from oraculo_contacts import __version__
from oraculo_contacts.application.review_workflow import preview_contacts
from oraculo_contacts.domain.changeset import PROTECTED_FIELDS, ChangeSet
from oraculo_contacts.domain.models import Contact
from oraculo_contacts.exceptions import ReportError


@dataclass(frozen=True, slots=True)
class ExportResult:
    """Rutas y checksums de una exportación terminada."""

    output: Path
    manifest: Path
    output_checksum: str


def export_copy(
    contacts: tuple[Contact, ...],
    changeset: ChangeSet,
    destination: Path,
    *,
    format_: str,
    source_filename: str,
    source_checksum: str,
    warnings: tuple[str, ...] = (),
    now: datetime | None = None,
) -> ExportResult:
    """Crear archivos nuevos y rechazar cualquier sobrescritura."""
    if format_ not in {"json", "csv", "vcf"}:
        raise ReportError("Formato de exportación no compatible.")
    folder = destination.expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    timestamp = (now or datetime.now(UTC)).strftime("%Y-%m-%d_%H%M")
    base = f"oraculo_contacts_revisado_{timestamp}"
    output = folder / f"{base}.{format_}"
    manifest = folder / f"{base}_manifest.json"
    if output.exists() or manifest.exists():
        raise ReportError("La exportación ya existe; ORÁCULO no sobrescribe archivos.")
    proposed = preview_contacts(contacts, changeset)
    content = _serialize(proposed, format_)
    try:
        output.write_text(content, encoding="utf-8", newline="")
        checksum = hashlib.sha256(output.read_bytes()).hexdigest()
        summary = changeset.summary()
        payload = {
            "source_file": Path(source_filename).name,
            "source_checksum": source_checksum,
            "output_file": output.name,
            "output_checksum": checksum,
            "approved_changes": summary.approved,
            "rejected_changes": summary.rejected,
            "protected_fields": sorted(PROTECTED_FIELDS),
            "oraculo_version": __version__,
            "generated_at": (now or datetime.now(UTC)).isoformat(),
            "warnings": list(warnings),
            "original_was_modified": False,
        }
        manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as error:
        output.unlink(missing_ok=True)
        manifest.unlink(missing_ok=True)
        raise ReportError(f"No se pudo exportar la copia: {error}") from error
    return ExportResult(output, manifest, checksum)


def _serialize(contacts: tuple[Contact, ...], format_: str) -> str:
    if format_ == "json":
        return json.dumps(
            {"contacts": [_contact_dict(item) for item in contacts]}, ensure_ascii=False, indent=2
        )
    if format_ == "csv":
        return _csv(contacts)
    return _vcf(contacts)


def _contact_dict(contact: Contact) -> dict[str, object]:
    return {
        "id": contact.source_id,
        "display_name": contact.display_name,
        "given_name": contact.given_name,
        "family_name": contact.family_name,
        "emails": list(contact.emails),
        "phones": list(contact.phones),
        "addresses": list(contact.addresses),
        "organization": contact.organization,
        "job_title": contact.job_title,
        "labels": list(contact.labels),
        "favorite": contact.favorite,
        "birthday": contact.birthday.isoformat() if contact.birthday else None,
        "notes": contact.notes,
    }


def _csv(contacts: tuple[Contact, ...]) -> str:
    output = io.StringIO(newline="")
    headers = [
        "Name",
        "Given Name",
        "Family Name",
        "E-mail 1 - Value",
        "E-mail 2 - Value",
        "Phone 1 - Value",
        "Phone 2 - Value",
        "Address 1 - Formatted",
        "Organization 1 - Name",
        "Organization 1 - Title",
        "Birthday",
        "Notes",
        "Labels",
    ]
    writer = csv.DictWriter(output, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    for contact in contacts:
        writer.writerow(
            {
                "Name": contact.display_name,
                "Given Name": contact.given_name,
                "Family Name": contact.family_name,
                "E-mail 1 - Value": contact.emails[0] if contact.emails else "",
                "E-mail 2 - Value": contact.emails[1] if len(contact.emails) > 1 else "",
                "Phone 1 - Value": contact.phones[0] if contact.phones else "",
                "Phone 2 - Value": contact.phones[1] if len(contact.phones) > 1 else "",
                "Address 1 - Formatted": contact.addresses[0] if contact.addresses else "",
                "Organization 1 - Name": contact.organization,
                "Organization 1 - Title": contact.job_title,
                "Birthday": contact.birthday.isoformat() if contact.birthday else "",
                "Notes": contact.notes or "",
                "Labels": ";".join(contact.labels),
            }
        )
    return output.getvalue()


def _vcf(contacts: tuple[Contact, ...]) -> str:
    cards: list[str] = []
    for contact in contacts:
        lines = [
            "BEGIN:VCARD",
            "VERSION:4.0",
            f"UID:{_escape(contact.source_id)}",
            f"FN:{_escape(contact.display_name)}",
            f"N:{_escape(contact.family_name)};{_escape(contact.given_name)};;;",
        ]
        lines.extend(f"TEL:{_escape(value)}" for value in contact.phones)
        lines.extend(f"EMAIL:{_escape(value)}" for value in contact.emails)
        lines.extend(f"ADR:;;{_escape(value)};;;;" for value in contact.addresses)
        if contact.organization:
            lines.append(f"ORG:{_escape(contact.organization)}")
        if contact.job_title:
            lines.append(f"TITLE:{_escape(contact.job_title)}")
        if contact.birthday:
            lines.append(f"BDAY:{contact.birthday.isoformat()}")
        if contact.notes:
            lines.append(f"NOTE:{_escape(contact.notes)}")
        if contact.labels:
            lines.append(f"CATEGORIES:{','.join(_escape(v) for v in contact.labels)}")
        lines.append("END:VCARD")
        cards.extend(lines)
    return "\r\n".join(cards) + "\r\n"


def _escape(value: str) -> str:
    return re.sub(r"([,;\\])", r"\\\1", value.replace("\n", "\\n"))
