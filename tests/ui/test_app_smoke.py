from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_visual_app_loads_demo_without_errors() -> None:
    app = Path(__file__).parents[2] / "src" / "oraculo_contacts" / "ui" / "app.py"
    test_app = AppTest.from_file(str(app), default_timeout=30).run()
    assert not test_app.exception
    assert any(title.value == "ORÁCULO CONTACTS" for title in test_app.title)
    assert any(header.value == "Resumen" for header in test_app.header)
    assert len(test_app.metric) == 11


def test_visual_navigation_opens_contacts() -> None:
    app = Path(__file__).parents[2] / "src" / "oraculo_contacts" / "ui" / "app.py"
    test_app = AppTest.from_file(str(app), default_timeout=30).run()
    navigation = next(radio for radio in test_app.radio if radio.label == "Navegación")
    navigation.set_value("Contactos").run()
    assert not test_app.exception
    assert any(header.value == "Contactos" for header in test_app.header)
    assert test_app.dataframe
