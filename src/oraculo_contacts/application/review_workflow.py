"""Aplicación de decisiones a copias y recuperación de la sesión."""

from __future__ import annotations

from dataclasses import dataclass, replace

from oraculo_contacts.domain.changeset import ChangeDecision, ChangeSet
from oraculo_contacts.domain.models import Contact


def preview_contacts(contacts: tuple[Contact, ...], changeset: ChangeSet) -> tuple[Contact, ...]:
    """Crear una agenda propuesta aplicando solo decisiones aprobadas a copias."""
    approved = [
        change
        for change in changeset.changes
        if change.decision is ChangeDecision.APPROVED and not change.protected
    ]
    by_ref: dict[str, list] = {}
    for change in approved:
        by_ref.setdefault(change.contact_ref, []).append(change)
    result: list[Contact] = []
    for contact in contacts:
        updated = contact
        for change in by_ref.get(contact.source_id, ()):
            updated = _apply(updated, change.field, change.before, change.after)
        result.append(updated)
    return tuple(result)


def _apply(contact: Contact, field: str, before: str, after: str) -> Contact:
    if field == "display_name":
        return replace(contact, display_name=after)
    if field == "organization":
        return replace(contact, organization=after)
    if field in {"email", "phone"}:
        attribute = "emails" if field == "email" else "phones"
        values = tuple(after if value == before else value for value in getattr(contact, attribute))
        return replace(contact, **{attribute: values})
    if field.startswith("address:"):
        index = int(field.split(":", 1)[1])
        values = list(contact.addresses)
        if index < len(values) and values[index] == before:
            values[index] = after
        return replace(contact, addresses=tuple(values))
    return contact


@dataclass(frozen=True, slots=True)
class DecisionHistory:
    """Historial inmutable de decisiones con deshacer y rehacer."""

    past: tuple[ChangeSet, ...]
    current: ChangeSet
    future: tuple[ChangeSet, ...] = ()

    def record(self, updated: ChangeSet) -> DecisionHistory:
        """Registrar una decisión nueva."""
        return DecisionHistory((*self.past, self.current), updated, ())

    def undo(self) -> DecisionHistory:
        """Deshacer la última decisión, no el archivo."""
        if not self.past:
            return self
        return DecisionHistory(self.past[:-1], self.past[-1], (self.current, *self.future))

    def redo(self) -> DecisionHistory:
        """Rehacer la próxima decisión disponible."""
        if not self.future:
            return self
        return DecisionHistory((*self.past, self.current), self.future[0], self.future[1:])
