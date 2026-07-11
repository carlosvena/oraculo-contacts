from oraculo_contacts.domain.models import Contact
from oraculo_contacts.domain.quality_analyzer import analyze_quality
from oraculo_contacts.presentation.quality_console_reporter import render_quality_console


def test_console_prioritizes_and_explains_duplicates() -> None:
    report = analyze_quality(
        (
            Contact("one", "Ada", emails=("same@example.test",)),
            Contact("two", "Ada", emails=("same@example.test",)),
        )
    )
    output = render_quality_console(report)
    assert "Score general:" in output
    assert "confianza" in output
    assert "Motivo:" in output
    assert "Recomendación:" in output
    assert "same@example.test" not in output
