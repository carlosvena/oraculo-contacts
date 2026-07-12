from contextlib import nullcontext
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
    process = SimpleNamespace(poll=lambda: None, wait=lambda: 0, returncode=None)
    monkeypatch.setattr(
        launcher.subprocess,
        "Popen",
        lambda command, **kwargs: recorded.append((command, kwargs)) or process,
    )
    response = SimpleNamespace(status=200)
    monkeypatch.setattr(
        launcher.urllib.request, "urlopen", lambda *args, **kwargs: nullcontext(response)
    )
    opened = []
    monkeypatch.setattr(launcher.webbrowser, "open", lambda url: opened.append(url))
    assert launcher.launch_ui() == 0
    assert recorded[0][0][1:4] == ["-m", "streamlit", "run"]
    assert recorded[0][1]["env"]["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] == "false"
    assert opened == ["http://localhost:8501"]
