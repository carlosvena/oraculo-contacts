from datetime import date

from oraculo_contacts.domain.models import Contact
from oraculo_contacts.ui.view_models import (
    PresenceFilter,
    QualityLevel,
    contact_summary,
    dashboard_metrics,
    filter_contacts,
    mask_email,
    mask_phone,
)


def _contacts() -> tuple[Contact, ...]:
    return (
        Contact(
            "one",
            "Ana Demo",
            emails=("ana@example.test",),
            phones=("+54 9 11 5555-0101",),
            addresses=("Calle Demo",),
            favorite=True,
            birthday=date(1990, 1, 1),
            notes="protected",
        ),
        Contact("two", "Sin Datos"),
    )


def test_dashboard_counts_visible_categories() -> None:
    metrics = dashboard_metrics(_contacts())
    assert metrics.contacts == 2
    assert metrics.favorites == 1
    assert metrics.birthdays == 1
    assert metrics.with_notes == 1
    assert metrics.phones == 1
    assert metrics.emails == 1
    assert metrics.addresses == 1
    assert 0 <= metrics.quality_score <= 100
    assert metrics.opportunities >= 1


def test_masks_personal_data_in_general_views() -> None:
    assert mask_email("ana@example.test") == "a•••@example.test"
    assert mask_email("invalid") == "••••"
    assert mask_phone("+54 9 11 5555-0101") == "•••• 0101"
    row = contact_summary(_contacts()[0], 95)
    assert row["Correo"] == "a•••@example.test"
    assert row["Teléfono"] == "•••• 0101"
    assert "ana@example.test" not in row.values()


def test_filters_by_query_presence_and_quality_without_mutation() -> None:
    contacts = _contacts()
    snapshot = repr(contacts)
    result = filter_contacts(
        contacts,
        query="ana",
        favorite=PresenceFilter.WITH,
        birthday=PresenceFilter.WITH,
        phone=PresenceFilter.WITH,
        email=PresenceFilter.WITH,
        quality=QualityLevel.HIGH,
    )
    assert result == (contacts[0],)
    assert filter_contacts(contacts, quality=QualityLevel.LOW) == (contacts[1],)
    assert repr(contacts) == snapshot
