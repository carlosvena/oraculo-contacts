from oraculo_contacts.domain.models import Contact
from oraculo_contacts.infrastructure.diagnostic_report import (
    diagnostic_payload,
    render_diagnostic_html,
    render_diagnostic_json,
)


def test_report_masks_sensitive_data_by_default() -> None:
    contact = Contact(
        "one",
        "Ada Demo",
        emails=("ada@example.test",),
        phones=("+54 9 11 5555-0101",),
        addresses=("Calle Privada",),
        notes="NOTA SECRETA",
    )
    payload = diagnostic_payload((contact,))
    output = render_diagnostic_json(payload) + render_diagnostic_html(payload)
    assert "ada@example.test" not in output
    assert "+54 9 11 5555-0101" not in output
    assert "Calle Privada" not in output
    assert "NOTA SECRETA" not in output
    assert payload["sensitive_data_included"] is False


def test_report_includes_sensitive_data_only_when_explicit() -> None:
    contact = Contact("one", "Ada", emails=("ada@example.test",), notes="Nota")
    payload = diagnostic_payload((contact,), include_sensitive=True)
    assert payload["contacts"][0]["emails"] == ["ada@example.test"]
    assert payload["contacts"][0]["notes"] == "Nota"
