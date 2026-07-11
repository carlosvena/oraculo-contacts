"""Contratos de infraestructura requeridos por la aplicación."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from oraculo_contacts.domain.models import Contact


class ContactImporter(Protocol):
    """Puerto de importación de contactos en modo lectura."""

    def load(self, source: Path) -> tuple[Contact, ...]:
        """Cargar una instantánea inmutable desde ``source``."""
        ...
