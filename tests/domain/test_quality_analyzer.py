from oraculo_contacts.domain.models import Contact, Severity
from oraculo_contacts.domain.quality_analyzer import analyze_quality


def test_detects_duplicate_with_reasons_confidence_and_severity() -> None:
    contacts = (
        Contact("one", "José Pérez", emails=("same@example.test",), phones=("0800-555-0101",)),
        Contact("two", "Jose Perez", emails=(" SAME@example.test ",), phones=("08005550101",)),
    )

    report = analyze_quality(contacts)

    candidate = report.duplicate_candidates[0]
    assert candidate.contact_refs == ("one", "two")
    assert candidate.matched_on == ("email", "phone", "name")
    assert candidate.confidence >= 0.98
    assert candidate.severity is Severity.ERROR
    assert len(candidate.reasons) == 3
    assert "no fusionar" in candidate.recommendation


def test_name_only_requires_high_similarity_and_has_explanation() -> None:
    report = analyze_quality((Contact("one", "Ada Lovelace"), Contact("two", "Ada Lovelac")))
    candidate = report.duplicate_candidates[0]
    assert candidate.matched_on == ("name",)
    assert 0.9 <= candidate.confidence < 0.97
    assert "%" in candidate.reasons[0]


def test_weak_name_similarity_is_not_a_candidate() -> None:
    report = analyze_quality((Contact("one", "Ada Lovelace"), Contact("two", "Ada Byron")))
    assert report.duplicate_candidates == ()


def test_scores_completeness_and_internal_inconsistencies() -> None:
    contact = Contact(
        "one",
        "Grace Hopper",
        given_name="Alan",
        family_name="Turing",
        emails=("invalid", "invalid"),
        phones=("12", "12"),
    )

    report = analyze_quality((contact,))

    assessment = report.contacts[0]
    assert assessment.completeness == 75
    assert 0 <= assessment.score < assessment.completeness <= 100
    assert {issue.code for issue in assessment.issues} == {
        "name_mismatch",
        "repeated_email",
        "repeated_phone",
        "invalid_email",
        "invalid_phone",
    }
    assert [item.priority for item in report.opportunities] == list(
        range(1, len(report.opportunities) + 1)
    )
    assert report.opportunities[0].severity is Severity.ERROR


def test_empty_collection_has_perfect_neutral_score() -> None:
    report = analyze_quality(())
    assert report.contacts_analyzed == 0
    assert report.quality_score == 100


def test_analysis_does_not_mutate_protected_or_other_fields() -> None:
    contact = Contact(
        "one",
        "Ada",
        emails=(" ADA@Example.test ",),
        favorite=True,
        notes="protected",
    )
    snapshot = repr(contact)
    analyze_quality((contact,))
    assert repr(contact) == snapshot
    assert contact.favorite is True
    assert contact.notes == "protected"
