"""Inicio controlado de la aplicación Streamlit."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

from oraculo_contacts.exceptions import OraculoError


def launch_ui() -> int:
    """Iniciar Streamlit con la aplicación incluida en el paquete."""
    if importlib.util.find_spec("streamlit") is None:
        raise OraculoError(
            'La interfaz no está instalada. Ejecute: python -m pip install -e ".[ui]"'
        )
    app_path = Path(__file__).with_name("app.py")
    environment = os.environ.copy()
    environment["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
        ],
        env=environment,
    )
    url = "http://localhost:8501"
    for _ in range(60):
        if process.poll() is not None:
            return process.returncode or 1
        try:
            with urllib.request.urlopen(f"{url}/_stcore/health", timeout=1) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return process.wait()
        except OSError:
            time.sleep(0.5)
    process.terminate()
    raise OraculoError("La interfaz no respondió en el puerto 8501.")
