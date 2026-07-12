"""Importador local de vCard 3.0 y 4.0 con recuperación parcial."""

from __future__ import annotations

import hashlib
import re
from datetime import date

from oraculo_contacts.domain.models import Contact
from oraculo_contacts.exceptions import ImportError
from oraculo_contacts.infrastructure.import_models import (
    ContactFormat,
    ImportResult,
    ImportWarning,
)

_KNOWN = {
    "VERSION",
    "FN",
    "N",
    "TEL",
    "EMAIL",
    "ADR",
    "ORG",
    "TITLE",
    "BDAY",
    "NOTE",
    "CATEGORIES",
    "UID",
}


class VCardImporter:
    """Interpretar propiedades conocidas sin descartar contactos recuperables."""

    def load_text(self, content: str) -> ImportResult:
        """Importar tarjetas desde UTF-8/BOM mantenido en memoria."""
        content = content.removeprefix("\ufeff")
        if not content.strip():
            raise ImportError("El archivo vCard está vacío.")
        lines = _unfold(content)
        cards = _cards(lines)
        if not cards:
            raise ImportError("No se encontraron bloques BEGIN:VCARD válidos.")
        contacts: list[Contact] = []
        warnings: list[ImportWarning] = []
        unknown: set[str] = set()
        recognized: set[str] = set()
        rejected = 0
        seen_ids: set[str] = set()
        for index, card in enumerate(cards, 1):
            contact, card_warnings, card_recognized, card_unknown = self._parse_card(
                card, index, seen_ids
            )
            warnings.extend(card_warnings)
            recognized.update(card_recognized)
            unknown.update(card_unknown)
            if contact is None:
                rejected += 1
            else:
                contacts.append(contact)
        return ImportResult(
            ContactFormat.VCARD,
            tuple(contacts),
            tuple(warnings),
            rejected,
            tuple(sorted(recognized)),
            tuple(sorted(unknown)),
        )

    def _parse_card(
        self, card: tuple[str, ...], index: int, seen_ids: set[str]
    ) -> tuple[Contact | None, tuple[ImportWarning, ...], set[str], set[str]]:
        location = f"tarjeta {index}"
        fields: dict[str, list[str]] = {}
        warnings: list[ImportWarning] = []
        recognized: set[str] = set()
        unknown: set[str] = set()
        for line in card:
            if ":" not in line:
                warnings.append(
                    ImportWarning(location, "invalid_line", "Se omitió una línea sin separador.")
                )
                continue
            descriptor, raw_value = line.split(":", 1)
            name = descriptor.split(";", 1)[0].split(".")[-1].upper()
            if name in _KNOWN:
                recognized.add(name.lower())
                fields.setdefault(name, []).append(_decode(raw_value))
                if "ENCODING=QUOTED-PRINTABLE" in descriptor.upper():
                    warnings.append(
                        ImportWarning(
                            location,
                            "unsupported_encoding",
                            "La codificación quoted-printable requiere revisión.",
                        )
                    )
            else:
                unknown.add(name)
        version = _first(fields, "VERSION")
        if version not in {"3.0", "4.0"}:
            warnings.append(
                ImportWarning(location, "unsupported_version", "La versión vCard no es 3.0 ni 4.0.")
            )
        structured = _first(fields, "N").split(";")
        family_name = structured[0] if structured else ""
        given_name = structured[1] if len(structured) > 1 else ""
        display_name = _first(fields, "FN") or " ".join(
            part for part in (given_name, family_name) if part
        )
        useful = display_name or fields.get("TEL") or fields.get("EMAIL") or fields.get("ORG")
        if not useful:
            warnings.append(
                ImportWarning(
                    location, "empty_card", "La tarjeta no contiene datos de contacto reconocibles."
                )
            )
            return None, tuple(warnings), recognized, unknown
        if not display_name:
            warnings.append(ImportWarning(location, "missing_name", "El contacto no tiene nombre."))
        birthday = _parse_birthday(_first(fields, "BDAY"), location, warnings)
        uid = _first(fields, "UID")
        source_id = _stable_id(uid or "\x1f".join(card), seen_ids)
        organization = _first(fields, "ORG").replace(";", " · ")
        addresses = tuple(_address(value) for value in fields.get("ADR", ()) if _address(value))
        labels = tuple(
            label.strip()
            for value in fields.get("CATEGORIES", ())
            for label in value.split(",")
            if label.strip()
        )
        return (
            Contact(
                source_id=source_id,
                display_name=display_name,
                given_name=given_name,
                family_name=family_name,
                emails=tuple(fields.get("EMAIL", ())),
                phones=tuple(_phone(value) for value in fields.get("TEL", ())),
                addresses=addresses,
                organization=organization,
                job_title=_first(fields, "TITLE"),
                labels=labels,
                favorite=any(
                    label.casefold() in {"starred", "favoritos", "destacados"} for label in labels
                ),
                birthday=birthday,
                notes=_first(fields, "NOTE") or None,
            ),
            tuple(warnings),
            recognized,
            unknown,
        )


def _unfold(content: str) -> tuple[str, ...]:
    unfolded: list[str] = []
    for raw_line in content.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw_line.startswith((" ", "\t")) and unfolded:
            unfolded[-1] += raw_line[1:]
        else:
            unfolded.append(raw_line)
    return tuple(unfolded)


def _cards(lines: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    cards: list[tuple[str, ...]] = []
    current: list[str] | None = None
    for line in lines:
        if line.upper() == "BEGIN:VCARD":
            current = []
        elif line.upper() == "END:VCARD" and current is not None:
            cards.append(tuple(current))
            current = None
        elif current is not None:
            current.append(line)
    return tuple(cards)


def _decode(value: str) -> str:
    return (
        value.replace("\\n", "\n")
        .replace("\\N", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
        .strip()
    )


def _first(fields: dict[str, list[str]], name: str) -> str:
    return fields.get(name, [""])[0]


def _parse_birthday(value: str, location: str, warnings: list[ImportWarning]) -> date | None:
    if not value:
        return None
    compact = re.sub(r"[^0-9]", "", value)
    if len(compact) == 8:
        try:
            return date(int(compact[:4]), int(compact[4:6]), int(compact[6:]))
        except ValueError:
            pass
    warnings.append(
        ImportWarning(location, "invalid_birthday", "El cumpleaños no pudo interpretarse.")
    )
    return None


def _address(value: str) -> str:
    return ", ".join(part for part in value.split(";") if part)


def _phone(value: str) -> str:
    return value.removeprefix("tel:")


def _stable_id(material: str, seen_ids: set[str]) -> str:
    base = f"vcf-{hashlib.sha256(material.encode('utf-8')).hexdigest()[:12]}"
    identifier = base
    suffix = 2
    while identifier in seen_ids:
        identifier = f"{base}-{suffix}"
        suffix += 1
    seen_ids.add(identifier)
    return identifier
