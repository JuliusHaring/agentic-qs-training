"""Wiederverwendbare Komposition für selbst implementierte Guardrails."""
from __future__ import annotations

from collections.abc import Iterable

from .domain import AgentDecision, GuardrailViolation, SupportRequest
from .ports import Guardrail, PolicyDecision


class GuardrailPipeline:
    """Führt Policies deterministisch aus; block hat Vorrang vor review und allow."""

    def __init__(self, guardrails: Iterable[Guardrail]) -> None:
        self.guardrails = list(guardrails)

    def evaluate(self, request: SupportRequest, decision: AgentDecision | None = None) -> PolicyDecision:
        review: PolicyDecision | None = None
        for guardrail in self.guardrails:
            result = guardrail.evaluate(request, decision)
            if result.action not in {"allow", "human_review", "block"}:
                raise GuardrailViolation(f"Ungültige Policy-Aktion von {result.policy}: {result.action}")
            if result.action == "block":
                return result
            if result.action == "human_review":
                review = result
        return review or PolicyDecision(action="allow", reason="Alle Policies erfüllt", policy="pipeline")
