"""Inicio controlado de la aplicación Streamlit."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

from oraculo_contacts.exceptions import OraculoError


def launch_ui() -> int:
    """Iniciar Streamlit con la aplicación incluida en el paquete."""
    if importlib.util.find_spec("streamlit") is None:
        raise OraculoError(
            'La interfaz no está instalada. Ejecute: python -m pip install -e ".[ui]"'
        )
    app_path = Path(__file__).with_name("app.py")
    return subprocess.call(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.headless=false",
            "--browser.gatherUsageStats=false",
        ]
    )
