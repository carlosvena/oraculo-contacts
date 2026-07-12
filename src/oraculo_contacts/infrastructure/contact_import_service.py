"""Detección de formato y fachada de importación local."""

from __future__ import annotations

from pathlib import Path

from oraculo_contacts.exceptions import ImportError
from oraculo_contacts.infrastructure.csv_importer import GoogleCsvImporter
from oraculo_contacts.infrastructure.import_models import ContactFormat, ImportResult
from oraculo_contacts.infrastructure.json_importer import JsonContactImporter
from oraculo_contacts.infrastructure.vcard_importer import VCardImporter


def detect_format(filename: str, content: str) -> ContactFormat:
    """Detectar formato por extensión y, como respaldo, por contenido."""
    suffix = Path(filename).suffix.casefold()
    stripped = content.lstrip("\ufeff\n\r\t ")
    if suffix == ".json" or stripped.startswith(("[", "{")):
        return ContactFormat.JSON
    if suffix in {".vcf", ".vcard"} or "BEGIN:VCARD" in content[:1024].upper():
        return ContactFormat.VCARD
    if suffix == ".csv" or ("," in content.partition("\n")[0]):
        return ContactFormat.GOOGLE_CSV
    raise ImportError("No se pudo detectar el formato. Use JSON, CSV, VCF o vCard.")


def import_contacts(filename: str, content: str) -> ImportResult:
    """Importar contenido en memoria sin escribir el archivo fuente."""
    format_ = detect_format(filename, content)
    if format_ is ContactFormat.GOOGLE_CSV:
        return GoogleCsvImporter().load_text(content)
    if format_ is ContactFormat.VCARD:
        return VCardImporter().load_text(content)
    contacts = JsonContactImporter().load_text(content, filename)
    return ImportResult(format_, contacts, (), 0, ("json_contact",), ())
