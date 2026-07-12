"""Hechos, evidencias y procedencia locales e inmutables."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class FactStatus(StrEnum):
    """Grado epistemológico de un hecho."""

    CONFIRMED = "confirmed"
    INFERRED = "inferred"


@dataclass(frozen=True, slots=True)
class Provenance:
    """Origen y momento de una observación."""

    source: str
    observed_at: datetime
    method: str

    @classmethod
    def now(cls, source: str, method: str) -> Provenance:
        """Crear procedencia con fecha UTC consciente."""
        return cls(source, datetime.now(UTC), method)


@dataclass(frozen=True, slots=True)
class Evidence:
    """Evidencia no sensible asociada a una regla determinista."""

    evidence_id: str
    contact_refs: tuple[str, ...]
    description: str
    provenance: Provenance


@dataclass(frozen=True, slots=True)
class Fact:
    """Afirmación trazable, confirmada o inferida."""

    fact_id: str
    subject_ref: str
    statement: str
    source: str
    recorded_at: datetime
    confidence: float
    evidence_ids: tuple[str, ...]
    status: FactStatus


class KnowledgeRegistry:
    """Registro en memoria sin persistencia implícita."""

    def __init__(self) -> None:
        """Inicializar un registro vacío."""
        self._evidence: dict[str, Evidence] = {}
        self._facts: dict[str, Fact] = {}

    def add_evidence(self, evidence: Evidence) -> None:
        """Registrar evidencia única."""
        if evidence.evidence_id in self._evidence:
            raise ValueError(f"Evidencia duplicada: {evidence.evidence_id}")
        self._evidence[evidence.evidence_id] = evidence

    def add_fact(self, fact: Fact) -> None:
        """Registrar un hecho solo si toda su evidencia existe."""
        missing = set(fact.evidence_ids) - self._evidence.keys()
        if missing:
            raise ValueError("El hecho referencia evidencia no registrada.")
        if fact.fact_id in self._facts:
            raise ValueError(f"Hecho duplicado: {fact.fact_id}")
        self._facts[fact.fact_id] = fact

    @property
    def evidence(self) -> tuple[Evidence, ...]:
        """Devolver una instantánea inmutable de evidencias."""
        return tuple(self._evidence.values())

    @property
    def facts(self) -> tuple[Fact, ...]:
        """Devolver una instantánea inmutable de hechos."""
        return tuple(self._facts.values())
