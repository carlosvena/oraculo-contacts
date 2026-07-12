"""Importador JSON estricto y exclusivamente de lectura."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from oraculo_contacts.domain.models import Contact
from oraculo_contacts.exceptions import ImportError


class JsonContactImporter:
    """Importar contactos desde JSON sin escribir nunca en el archivo fuente."""

    def load(self, source: Path) -> tuple[Contact, ...]:
        """Leer y validar contactos desde una ruta regular existente."""
        if not source.is_file():
            raise ImportError(f"El archivo de entrada no existe o no es regular: {source}")
        try:
            with source.open("r", encoding="utf-8") as stream:
                payload = json.load(stream)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ImportError(f"No se pudo leer JSON válido desde {source}: {error}") from error

        return self._parse_payload(payload)

    def load_text(self, content: str, label: str = "archivo cargado") -> tuple[Contact, ...]:
        """Validar JSON recibido en memoria sin crear ni modificar archivos."""
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as error:
            raise ImportError(f"No se pudo leer JSON válido desde {label}: {error}") from error
        return self._parse_payload(payload)

    def _parse_payload(self, payload: Any) -> tuple[Contact, ...]:
        """Validar la raíz y convertir todos los registros."""
        raw_contacts = payload.get("contacts") if isinstance(payload, dict) else payload
        if not isinstance(raw_contacts, list):
            raise ImportError(
                "La raíz JSON debe ser una lista o un objeto con una lista 'contacts'."
            )
        return tuple(self._parse_contact(item, index) for index, item in enumerate(raw_contacts))

    def _parse_contact(self, item: Any, index: int) -> Contact:
        """Convertir un objeto JSON validado a una entidad inmutable."""
        if not isinstance(item, dict):
            raise ImportError(f"El contacto en la posición {index} debe ser un objeto.")
        source_id = item.get("id", f"record-{index + 1}")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ImportError(f"El campo 'id' del contacto {index} debe ser una cadena no vacía.")
        birthday = self._optional_date(item.get("birthday"), index)
        favorite = item.get("favorite", False)
        notes = item.get("notes")
        if not isinstance(favorite, bool):
            raise ImportError(f"El campo 'favorite' del contacto {index} debe ser booleano.")
        if notes is not None and not isinstance(notes, str):
            raise ImportError(f"El campo 'notes' del contacto {index} debe ser texto o null.")
        return Contact(
            source_id=source_id,
            display_name=self._text(item, "display_name", index),
            given_name=self._text(item, "given_name", index),
            family_name=self._text(item, "family_name", index),
            emails=self._strings(item, "emails", index),
            phones=self._strings(item, "phones", index),
            addresses=self._strings(item, "addresses", index),
            favorite=favorite,
            birthday=birthday,
            notes=notes,
        )

    @staticmethod
    def _text(item: dict[str, Any], field: str, index: int) -> str:
        value = item.get(field, "")
        if not isinstance(value, str):
            raise ImportError(f"El campo '{field}' del contacto {index} debe ser texto.")
        return value

    @staticmethod
    def _strings(item: dict[str, Any], field: str, index: int) -> tuple[str, ...]:
        value = item.get(field, [])
        if not isinstance(value, list) or any(not isinstance(entry, str) for entry in value):
            raise ImportError(
                f"El campo '{field}' del contacto {index} debe ser una lista de textos."
            )
        return tuple(value)

    @staticmethod
    def _optional_date(value: Any, index: int) -> date | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ImportError(f"El campo 'birthday' del contacto {index} debe ser una fecha ISO.")
        try:
            return date.fromisoformat(value)
        except ValueError as error:
            raise ImportError(
                f"El campo 'birthday' del contacto {index} debe usar AAAA-MM-DD."
            ) from error
