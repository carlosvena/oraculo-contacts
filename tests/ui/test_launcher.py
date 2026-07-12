from types import SimpleNamespace

import pytest

from oraculo_contacts.exceptions import OraculoError
from oraculo_contacts.ui import launcher


def test_launcher_explains_missing_ui_dependency(monkeypatch) -> None:
    monkeypatch.setattr(launcher.importlib.util, "find_spec", lambda _name: None)
    with pytest.raises(OraculoError, match="interfaz no está instalada"):
        launcher.launch_ui()


def test_launcher_invokes_streamlit_module(monkeypatch) -> None:
    monkeypatch.setattr(launcher.importlib.util, "find_spec", lambda _name: SimpleNamespace())
    recorded = []
    monkeypatch.setattr(launcher.subprocess, "call", lambda command: recorded.append(command) or 0)
    assert launcher.launch_ui() == 0
    assert recorded[0][1:4] == ["-m", "streamlit", "run"]
