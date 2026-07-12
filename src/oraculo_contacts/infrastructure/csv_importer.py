"""Importador local y tolerante de Google Contacts CSV."""

from __future__ import annotations

import csv
import hashlib
import io
import re
import unicodedata
from datetime import date

from oraculo_contacts.domain.models import Contact
from oraculo_contacts.exceptions import ImportError
from oraculo_contacts.infrastructure.import_models import (
    ContactFormat,
    ImportResult,
    ImportWarning,
)

_ALIASES = {
    "name": {"name", "nombre"},
    "given_name": {"given name", "nombre de pila", "primer nombre"},
    "family_name": {"family name", "apellidos", "apellido"},
    "birthday": {"birthday", "cumpleanos"},
    "notes": {"notes", "notas"},
    "labels": {"labels", "etiquetas"},
}


class GoogleCsvImporter:
    """Leer exportaciones CSV sin detenerse por filas parciales."""

    def load_text(self, content: str) -> ImportResult:
        """Importar UTF-8/BOM desde memoria y conservar advertencias seguras."""
        content = content.removeprefix("\ufeff")
        if not content.strip():
            raise ImportError("El archivo CSV está vacío.")
        try:
            reader = csv.DictReader(io.StringIO(content))
            headers = tuple(reader.fieldnames or ())
            if not headers:
                raise ImportError("El CSV no contiene encabezados.")
            mapping = {header: _field_kind(header) for header in headers}
            recognized = tuple(sorted({kind for kind in mapping.values() if kind is not None}))
            unknown = tuple(header for header, kind in mapping.items() if kind is None)
            contacts: list[Contact] = []
            warnings: list[ImportWarning] = []
            rejected = 0
            seen_ids: set[str] = set()
            for row_number, row in enumerate(reader, 2):
                contact, row_warnings = self._parse_row(row, mapping, row_number, seen_ids)
                warnings.extend(row_warnings)
                if contact is None:
                    rejected += 1
                else:
                    contacts.append(contact)
            return ImportResult(
                ContactFormat.GOOGLE_CSV,
                tuple(contacts),
                tuple(warnings),
                rejected,
                recognized,
                unknown,
            )
        except csv.Error as error:
            raise ImportError(f"El CSV no pudo interpretarse: {error}") from error

    def _parse_row(
        self,
        row: dict[str | None, str | list[str] | None],
        mapping: dict[str, str | None],
        row_number: int,
        seen_ids: set[str],
    ) -> tuple[Contact | None, tuple[ImportWarning, ...]]:
        values: dict[str, list[str]] = {}
        location = f"fila {row_number}"
        warnings: list[ImportWarning] = []
        for header, raw_value in row.items():
            if header is None or not isinstance(raw_value, str):
                warnings.append(
                    ImportWarning(
                        location,
                        "extra_columns",
                        "La fila contiene columnas adicionales y fueron ignoradas.",
                    )
                )
                continue
            kind = mapping.get(header)
            value = (raw_value or "").strip()
            if kind and value:
                values.setdefault(kind, []).append(value)
        if not values:
            warning = ImportWarning(location, "empty_row", "La fila no contiene datos reconocidos.")
            return None, (*warnings, warning)
        display_name = _first(values, "name") or " ".join(
            part for part in (_first(values, "given_name"), _first(values, "family_name")) if part
        )
        if not display_name:
            warnings.append(ImportWarning(location, "missing_name", "El contacto no tiene nombre."))
        birthday = _birthday(_first(values, "birthday"), location, warnings)
        source_id = _stable_id(row, seen_ids)
        return (
            Contact(
                source_id=source_id,
                display_name=display_name,
                given_name=_first(values, "given_name"),
                family_name=_first(values, "family_name"),
                emails=tuple(values.get("email", ())),
                phones=tuple(values.get("phone", ())),
                addresses=tuple(values.get("address", ())),
                organization=_first(values, "organization"),
                job_title=_first(values, "job_title"),
                labels=_split_labels(values.get("labels", ())),
                birthday=birthday,
                notes=_first(values, "notes") or None,
            ),
            tuple(warnings),
        )


def _field_kind(header: str) -> str | None:
    normalized = _normalize_header(header)
    for kind, aliases in _ALIASES.items():
        if normalized in aliases:
            return kind
    if re.match(r"^(e-?mail|correo electronico|correo) \d+", normalized):
        return "email" if "value" in normalized or "valor" in normalized else None
    if re.match(r"^(phone|telefono) \d+", normalized):
        return "phone" if "value" in normalized or "valor" in normalized else None
    if re.match(r"^(address|direccion) \d+", normalized):
        return (
            "address"
            if any(term in normalized for term in ("formatted", "formateada", "valor"))
            else None
        )
    if re.match(r"^(organization|organizacion) \d+", normalized):
        if normalized.endswith(("name", "nombre")):
            return "organization"
        if normalized.endswith(("title", "cargo")):
            return "job_title"
    return None


def _normalize_header(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return " ".join(
        "".join(
            character for character in decomposed if not unicodedata.combining(character)
        ).split()
    )


def _first(values: dict[str, list[str]], field: str) -> str:
    return values.get(field, [""])[0]


def _birthday(value: str, location: str, warnings: list[ImportWarning]) -> date | None:
    if not value:
        return None
    for candidate in (value, value.replace("/", "-")):
        try:
            return date.fromisoformat(candidate)
        except ValueError:
            continue
    warnings.append(
        ImportWarning(location, "invalid_birthday", "El cumpleaños no es una fecha ISO.")
    )
    return None


def _stable_id(row: dict[str | None, str | list[str] | None], seen_ids: set[str]) -> str:
    material = "\x1f".join(
        value.strip()
        for key, value in sorted(row.items(), key=lambda item: item[0] or "")
        if key is not None and isinstance(value, str)
    )
    base = f"csv-{hashlib.sha256(material.encode('utf-8')).hexdigest()[:12]}"
    identifier = base
    suffix = 2
    while identifier in seen_ids:
        identifier = f"{base}-{suffix}"
        suffix += 1
    seen_ids.add(identifier)
    return identifier


def _split_labels(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        label.strip() for value in values for label in re.split(r"[;,]", value) if label.strip()
    )
