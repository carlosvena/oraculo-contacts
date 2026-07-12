from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_visual_app_loads_demo_without_errors() -> None:
    app = Path(__file__).parents[2] / "src" / "oraculo_contacts" / "ui" / "app.py"
    test_app = AppTest.from_file(str(app), default_timeout=30).run()
    demo = next(
        button for button in test_app.button if button.label == "Probar con datos de demostración"
    )
    demo.click().run()
    assert not test_app.exception
    assert any(title.value == "ORÁCULO CONTACTS" for title in test_app.title)
    assert any(header.value == "Resumen" for header in test_app.header)
    assert len(test_app.metric) == 14


def test_visual_navigation_opens_contacts() -> None:
    app = Path(__file__).parents[2] / "src" / "oraculo_contacts" / "ui" / "app.py"
    test_app = AppTest.from_file(str(app), default_timeout=30).run()
    next(
        button for button in test_app.button if button.label == "Probar con datos de demostración"
    ).click().run()
    navigation = next(radio for radio in test_app.radio if radio.label == "Navegación")
    navigation.set_value("Contactos").run()
    assert not test_app.exception
    assert any(header.value == "Contactos" for header in test_app.header)
    assert test_app.dataframe


def test_closing_session_returns_to_import_screen() -> None:
    app = Path(__file__).parents[2] / "src" / "oraculo_contacts" / "ui" / "app.py"
    test_app = AppTest.from_file(str(app), default_timeout=30).run()
    next(
        button for button in test_app.button if button.label == "Probar con datos de demostración"
    ).click().run()
    next(
        button
        for button in test_app.button
        if button.label == "Cerrar sesión y borrar datos temporales"
    ).click().run()
    assert not test_app.exception
    assert any(button.label == "Importar Google Contacts CSV" for button in test_app.button)


def test_visual_review_and_preview_pages_load() -> None:
    app = Path(__file__).parents[2] / "src" / "oraculo_contacts" / "ui" / "app.py"
    test_app = AppTest.from_file(str(app), default_timeout=30).run()
    next(
        button for button in test_app.button if button.label == "Probar con datos de demostración"
    ).click().run()
    navigation = next(radio for radio in test_app.radio if radio.label == "Navegación")
    navigation.set_value("Revisión de cambios").run()
    assert not test_app.exception
    assert any(header.value == "Revisión de cambios" for header in test_app.header)
    navigation = next(radio for radio in test_app.radio if radio.label == "Navegación")
    navigation.set_value("Vista previa del resultado").run()
    assert not test_app.exception
    assert any(header.value == "Vista previa del resultado" for header in test_app.header)
