"""Workspace local opcional con consentimiento explícito."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from oraculo_contacts.domain.models import Contact
from oraculo_contacts.exceptions import ReportError


def source_checksum(content: bytes) -> str:
    """Calcular SHA-256 sin registrar ni transmitir el contenido."""
    return hashlib.sha256(content).hexdigest()


def save_workspace(
    contacts: tuple[Contact, ...],
    destination: Path,
    *,
    source_sha256: str,
    repository_root: Path,
) -> Path:
    """Guardar una copia local solo en una ruta consentida fuera del repositorio.

    Las notas se omiten deliberadamente porque pueden contener secretos o texto libre sensible.
    """
    resolved = destination.expanduser().resolve()
    root = repository_root.resolve()
    if resolved == root or root in resolved.parents:
        raise ReportError("La sesión debe guardarse fuera del repositorio.")
    resolved.mkdir(parents=True, exist_ok=True)
    output = resolved / "oraculo-session.json"
    payload: dict[str, Any] = {
        "schema_version": "workspace-1.0",
        "imported_at": datetime.now(UTC).isoformat(),
        "source_sha256": source_sha256,
        "notes_omitted": True,
        "contacts": [
            {
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
            }
            for contact in contacts
        ],
    }
    try:
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as error:
        raise ReportError(f"No se pudo guardar la sesión local: {error}") from error
    return output
