"""PydanticAI factories and dependencies shared by the progressive exercises."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.test import TestModel

from .domain import AgentDecision
from .providers import SYSTEM_PROMPT
from .tools import HttpTransport


@dataclass
class SupportDependencies:
    """Runtime dependencies injected into instructions, validators, and tools."""

    customer_id: str
    actor_roles: set[str] = field(default_factory=lambda: {"support_agent"})
    transport: HttpTransport | None = None
    automation_threshold: float = 0.80
    audit_log: list[dict[str, Any]] = field(default_factory=list)


def structured_test_model(category: str = "technical", priority: str = "medium", confidence: float = 0.91) -> TestModel:
    """Deterministic stand-in; production can inject an OpenAI/Anthropic model name."""
    return TestModel(
        custom_output_args={
            "category": category,
            "priority": priority,
            "reason": "Die Anfrage enthält eindeutige fachliche Schlüsselbegriffe.",
            "confidence": confidence,
        }
    )


def create_decision_agent(model: Any = None) -> Agent[SupportDependencies, AgentDecision]:
    agent = Agent(
        model or structured_test_model(),
        deps_type=SupportDependencies,
        output_type=AgentDecision,
        system_prompt=SYSTEM_PROMPT,
        retries=2,
        name="support_classifier",
    )

    @agent.output_validator
    def validate_decision(ctx: RunContext[SupportDependencies], output: AgentDecision) -> AgentDecision:
        if output.priority.value == "high" and output.confidence < 0.75:
            raise ModelRetry("Hohe Priorität erfordert confidence >= 0.75")
        ctx.deps.audit_log.append({"event": "decision_validated", "confidence": output.confidence})
        return output

    return agent
