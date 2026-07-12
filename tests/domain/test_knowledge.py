from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from oraculo_contacts.domain.knowledge import (
    Evidence,
    Fact,
    FactStatus,
    KnowledgeRegistry,
    Provenance,
)


def test_registry_preserves_traceable_fact_in_memory() -> None:
    provenance = Provenance("contacts.json", datetime.now(UTC), "deterministic_rule")
    evidence = Evidence("e-1", ("one",), "Formato observado por una regla local.", provenance)
    fact = Fact(
        "f-1",
        "one",
        "El nombre admite una propuesta de normalización.",
        "normalization_engine",
        datetime.now(UTC),
        0.93,
        ("e-1",),
        FactStatus.INFERRED,
    )
    registry = KnowledgeRegistry()
    registry.add_evidence(evidence)
    registry.add_fact(fact)
    assert registry.evidence == (evidence,)
    assert registry.facts == (fact,)
    with pytest.raises(FrozenInstanceError):
        fact.statement = "changed"  # type: ignore[misc]


def test_registry_rejects_missing_or_duplicate_evidence() -> None:
    registry = KnowledgeRegistry()
    fact = Fact(
        "f-1",
        "one",
        "Statement",
        "test",
        datetime.now(UTC),
        1.0,
        ("missing",),
        FactStatus.CONFIRMED,
    )
    with pytest.raises(ValueError, match="no registrada"):
        registry.add_fact(fact)
    evidence = Evidence("e-1", ("one",), "Description", Provenance.now("test", "rule"))
    registry.add_evidence(evidence)
    with pytest.raises(ValueError, match="duplicada"):
        registry.add_evidence(evidence)
