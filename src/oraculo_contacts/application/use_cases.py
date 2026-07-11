"""Casos de uso públicos de ORÁCULO CONTACTS."""

from __future__ import annotations

from pathlib import Path

from oraculo_contacts.application.ports import ContactImporter
from oraculo_contacts.domain.auditor import audit_contacts
from oraculo_contacts.domain.models import AuditReport


class AuditContacts:
    """Orquestar la importación y auditoría sin modificar el origen."""

    def __init__(self, importer: ContactImporter) -> None:
        """Inicializar con un importador que satisface el puerto de lectura."""
        self._importer = importer

    def execute(self, source: Path) -> AuditReport:
        """Auditar la instantánea importada desde ``source``."""
        contacts = self._importer.load(source)
        return AuditReport.create(len(contacts), audit_contacts(contacts))
