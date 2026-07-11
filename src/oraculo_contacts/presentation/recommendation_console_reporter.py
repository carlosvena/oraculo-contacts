"""Presentación de planes de acción para revisión humana."""

from __future__ import annotations

from oraculo_contacts.domain.recommendations import ActionPlan


def render_action_plan_console(plan: ActionPlan) -> str:
    """Renderizar prioridades y explicar que ninguna recomendación se ejecuta."""
    protected = ", ".join(plan.protected_fields_involved) or "ninguno"
    lines = [
        "ORÁCULO CONTACTS — Plan de mejora seguro",
        f"Contactos analizados: {plan.contacts_analyzed}",
        f"Recomendaciones: {len(plan.recommendations)}",
        f"Tiempo estimado: {plan.estimated_minutes} minutos",
        f"Riesgo general: {plan.overall_risk.value}",
        f"Campos protegidos involucrados: {protected}",
        f"Explicación: {plan.explanation}",
    ]
    if plan.top_problems:
        lines.extend(("", "Principales problemas:"))
        lines.extend(f"- {problem}" for problem in plan.top_problems)
    if plan.recommendations:
        lines.extend(("", "Mejores oportunidades:"))
        for index, item in enumerate(plan.recommendations, 1):
            lines.append(
                f"{index}. {item.title} | prioridad {item.priority_score:.2f} | "
                f"confianza {item.confidence:.0%} | riesgo {item.risk.value}"
            )
            lines.append(f"   {item.explanation}")
    lines.extend(("", "Ninguna recomendación fue ejecutada."))
    return "\n".join(lines) + "\n"
