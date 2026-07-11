"""Configuración centralizada de logging seguro."""

from __future__ import annotations

import logging
from typing import Final

_FORMAT: Final = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(verbose: bool = False) -> None:
    """Configurar logs operativos; los llamadores no deben registrar datos de contactos."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format=_FORMAT,
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        force=True,
    )
