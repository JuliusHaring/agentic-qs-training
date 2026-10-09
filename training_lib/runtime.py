"""Produktionsnahe Basisklassen für Agenten-Pipelines."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from .domain import AgentDecision, AgentResponse, GuardrailViolation, SupportRequest
from .ports import Guardrail, PolicyDecision, StructuredModelPort
from .providers import SYSTEM_PROMPT


class BaseSupportAgent(ABC):
    """Template Method: Unterklassen implementieren die Evolutionsstufe."""

    @abstractmethod
    def run(self, request: SupportRequest) -> AgentResponse:
        raise NotImplementedError


class StructuredSupportAgent(BaseSupportAgent):
    def __init__(self, model: StructuredModelPort) -> None:
        self.model = model

    def classify(self, request: SupportRequest) -> AgentDecision:
        return self.model.complete_structured(SYSTEM_PROMPT, request.message, AgentDecision)

    def validate_business_rules(self, decision: AgentDecision) -> None:
        if decision.priority.value == "high" and decision.confidence < 0.75:
            raise ValueError("Hohe Priorität erfordert mindestens 0.75 Confidence")

    def run(self, request: SupportRequest) -> AgentResponse:
        try:
            decision = self.classify(request)
            self.validate_business_rules(decision)
            return AgentResponse(request_id=request.request_id, status="completed", decision=decision)
        except Exception as error:
            return AgentResponse(request_id=request.request_id, status="failed", diagnostics={"error": type(error).__name__, "message": str(error)})


class GuardedSupportAgent(StructuredSupportAgent):
    def __init__(self, model: StructuredModelPort, guardrails: Iterable[Guardrail]) -> None:
        super().__init__(model)
        self.guardrails = list(guardrails)

    def evaluate_policies(self, request: SupportRequest, decision: AgentDecision | None) -> PolicyDecision:
        review: PolicyDecision | None = None
        for guardrail in self.guardrails:
            result = guardrail.evaluate(request, decision)
            if result.action == "block":
                raise GuardrailViolation(f"{result.policy}: {result.reason}")
            if result.action == "human_review":
                review = result
        return review or PolicyDecision(action="allow", reason="Alle Policies erfüllt", policy="pipeline")

    def run(self, request: SupportRequest) -> AgentResponse:
        try:
            self.evaluate_policies(request, None)
            decision = self.classify(request)
            self.validate_business_rules(decision)
            policy = self.evaluate_policies(request, decision)
            status = "human_review" if policy.action == "human_review" else "completed"
            return AgentResponse(request_id=request.request_id, status=status, decision=decision, diagnostics={"policy": policy.model_dump()})
        except GuardrailViolation as error:
            return AgentResponse(request_id=request.request_id, status="rejected", diagnostics={"error": str(error)})
        except Exception as error:
            return AgentResponse(request_id=request.request_id, status="failed", diagnostics={"error": type(error).__name__, "message": str(error)})
