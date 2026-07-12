from oraculo_contacts.domain.models import Contact
from oraculo_contacts.domain.recommendations import RecommendationEngine
from oraculo_contacts.presentation.recommendation_console_reporter import (
    render_action_plan_console,
)


def test_console_explains_plan_and_non_execution() -> None:
    plan = RecommendationEngine().build_plan((Contact("one", "  ada "),))
    output = render_action_plan_console(plan)
    assert "Tiempo estimado:" in output
    assert "riesgo low" in output
    assert "Ninguna recomendación fue ejecutada" in output


def test_console_handles_empty_plan() -> None:
    output = render_action_plan_console(RecommendationEngine().build_plan(()))
    assert "Recomendaciones: 0" in output
    assert "Principales problemas:" not in output
