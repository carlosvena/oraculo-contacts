from oraculo_contacts.domain.models import AuditReport, Finding, FindingCode, Severity
from oraculo_contacts.presentation.console_reporter import render_console


def test_renders_summary_and_safe_references() -> None:
    report = AuditReport.create(
        2,
        (
            Finding(
                FindingCode.POSSIBLE_DUPLICATE_EMAIL,
                Severity.WARNING,
                ("one", "two"),
                "Posible duplicado.",
            ),
        ),
    )
    output = render_console(report)
    assert "Contactos analizados: 2" in output
    assert "one, two" in output
    assert "advertencias: 1" in output


def test_renders_clean_report() -> None:
    output = render_console(AuditReport.create(0, ()))
    assert "No se detectaron problemas" in output
