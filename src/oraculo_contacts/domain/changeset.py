"""Revisión inmutable de cambios aprobados exclusivamente por una persona."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum

from oraculo_contacts.domain.models import Contact
from oraculo_contacts.domain.proposals import ProposalRisk, propose_contact_normalizations
from oraculo_contacts.domain.quality_analyzer import analyze_quality

PROTECTED_FIELDS = frozenset(
    {"favorite", "birthday", "notes", "photo", "external_id", "sensitive_labels"}
)


class ChangeDecision(StrEnum):
    """Decisión humana sobre una propuesta."""

    PENDING = "pendiente"
    APPROVED = "aprobada"
    REJECTED = "rechazada"
    POSTPONED = "pospuesta"
    CONFLICT = "conflictiva"
    BLOCKED = "bloqueada"


@dataclass(frozen=True, slots=True)
class ProposedChange:
    """Propuesta trazable que no altera el contacto original."""

    change_id: str
    contact_ref: str
    category: str
    field: str
    before: str
    after: str
    created_at: datetime
    source: str
    evidence: tuple[str, ...]
    confidence: float
    risk: ProposalRisk
    decision: ChangeDecision
    reason: str
    rule_version: str
    estimated_impact: int
    protected: bool = False


@dataclass(frozen=True, slots=True)
class ChangeConflict:
    """Cambios aprobados incompatibles sobre el mismo campo."""

    contact_ref: str
    field: str
    change_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProtectedFieldViolation:
    """Intento bloqueado de aprobación no individual."""

    change_id: str
    field: str
    reason: str


@dataclass(frozen=True, slots=True)
class ChangeSetSummary:
    """Conteos inmutables del estado de revisión."""

    total: int
    approved: int
    rejected: int
    postponed: int
    pending: int
    blocked: int
    conflicts: int
    contacts_affected: int


@dataclass(frozen=True, slots=True)
class ChangeSet:
    """Colección versionada de decisiones sin mutación interna."""

    changes: tuple[ProposedChange, ...]

    def decide(
        self, change_id: str, decision: ChangeDecision, *, individual_protected: bool = False
    ) -> ChangeSet:
        """Devolver una copia con una decisión humana nueva."""
        updated: list[ProposedChange] = []
        found = False
        for change in self.changes:
            if change.change_id != change_id:
                updated.append(change)
                continue
            found = True
            if (
                change.protected
                and decision is ChangeDecision.APPROVED
                and not individual_protected
            ):
                raise ValueError("Un campo protegido requiere aprobación individual explícita.")
            updated.append(replace(change, decision=decision))
        if not found:
            raise KeyError(change_id)
        return ChangeSet(tuple(updated))

    def approve_low_risk(self) -> ChangeSet:
        """Aprobar masivamente solo cambios de bajo riesgo no protegidos."""
        return ChangeSet(
            tuple(
                replace(change, decision=ChangeDecision.APPROVED)
                if change.risk is ProposalRisk.LOW
                and not change.protected
                and change.decision is ChangeDecision.PENDING
                else change
                for change in self.changes
            )
        )

    def restore(self) -> ChangeSet:
        """Restaurar propuestas revisables a pendientes y protegidas a bloqueadas."""
        return ChangeSet(
            tuple(
                replace(
                    change,
                    decision=(
                        ChangeDecision.BLOCKED if change.protected else ChangeDecision.PENDING
                    ),
                )
                for change in self.changes
            )
        )

    def discard(self) -> ChangeSet:
        """Descartar completamente el conjunto."""
        return ChangeSet(())

    def conflicts(self) -> tuple[ChangeConflict, ...]:
        """Detectar aprobaciones incompatibles del mismo campo."""
        groups: dict[tuple[str, str], list[ProposedChange]] = {}
        for change in self.changes:
            if change.decision is ChangeDecision.APPROVED:
                groups.setdefault((change.contact_ref, change.field), []).append(change)
        return tuple(
            ChangeConflict(ref, field, tuple(item.change_id for item in items))
            for (ref, field), items in groups.items()
            if len({item.after for item in items}) > 1
        )

    def validate(self) -> tuple[ProtectedFieldViolation, ...]:
        """Informar cualquier campo protegido aprobado indebidamente."""
        return tuple(
            ProtectedFieldViolation(change.change_id, change.field, "Campo protegido aprobado.")
            for change in self.changes
            if change.protected and change.decision is ChangeDecision.APPROVED
        )

    def summary(self) -> ChangeSetSummary:
        """Resumir decisiones y contactos afectados."""
        counts = {decision: 0 for decision in ChangeDecision}
        for change in self.changes:
            counts[change.decision] += 1
        return ChangeSetSummary(
            len(self.changes),
            counts[ChangeDecision.APPROVED],
            counts[ChangeDecision.REJECTED],
            counts[ChangeDecision.POSTPONED],
            counts[ChangeDecision.PENDING],
            counts[ChangeDecision.BLOCKED],
            len(self.conflicts()),
            len({item.contact_ref for item in self.changes}),
        )


def build_changeset(contacts: tuple[Contact, ...]) -> ChangeSet:
    """Convertir motores existentes en propuestas revisables."""
    changes: list[ProposedChange] = []
    now = datetime.now(UTC)
    for contact in contacts:
        for proposal in propose_contact_normalizations(contact):
            changes.append(
                ProposedChange(
                    f"change-{len(changes) + 1}",
                    contact.source_id,
                    _category(proposal.field),
                    proposal.field,
                    proposal.original_value,
                    proposal.proposed_value,
                    now,
                    "normalization_engine",
                    (proposal.reason,),
                    proposal.confidence,
                    proposal.risk,
                    ChangeDecision.PENDING,
                    proposal.reason,
                    "normalization-1.0",
                    40 if proposal.risk is ProposalRisk.LOW else 25,
                )
            )
        for field, value in (
            ("organization", contact.organization),
            *tuple((f"address:{i}", value) for i, value in enumerate(contact.addresses)),
        ):
            trimmed = " ".join(value.split())
            if value and trimmed != value:
                changes.append(
                    _simple_change(len(changes) + 1, contact.source_id, field, value, trimmed, now)
                )
    quality = analyze_quality(contacts)
    for duplicate in quality.duplicate_candidates:
        changes.append(
            ProposedChange(
                f"change-{len(changes) + 1}",
                duplicate.contact_refs[0],
                "duplicados potenciales",
                "duplicate_review",
                " · ".join(duplicate.contact_refs),
                "Revisión manual requerida",
                now,
                "quality_analyzer",
                duplicate.reasons,
                duplicate.confidence,
                ProposalRisk.HIGH,
                ChangeDecision.CONFLICT,
                "ORÁCULO no fusiona automáticamente.",
                "duplicates-1.0",
                0,
            )
        )
    return ChangeSet(tuple(changes))


def _simple_change(
    sequence: int, ref: str, field: str, before: str, after: str, now: datetime
) -> ProposedChange:
    category = "organizaciones" if field == "organization" else "direcciones"
    return ProposedChange(
        f"change-{sequence}",
        ref,
        category,
        field,
        before,
        after,
        now,
        "safe_trim_rule",
        ("Se detectaron espacios redundantes.",),
        0.99,
        ProposalRisk.LOW,
        ChangeDecision.PENDING,
        "Quitar espacios redundantes.",
        "trim-1.0",
        20,
    )


def _category(field: str) -> str:
    return {"display_name": "nombres", "phone": "teléfonos", "email": "correos"}.get(
        field, "inconsistencias"
    )
