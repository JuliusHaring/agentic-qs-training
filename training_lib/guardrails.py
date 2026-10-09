"""Einfache, explizite Policies für Input und Agentenaktionen."""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel

from .models import AgentDecision, SupportRequest


class GuardrailResult(BaseModel):
    action: Literal["allow", "human_review", "block"]
    reason: str


INJECTION_PATTERNS = (r"ignore (all|previous)", r"system prompt", r"export .*data", r"developer message")


def evaluate_guardrails(request: SupportRequest, decision: AgentDecision) -> GuardrailResult:
    if any(re.search(pattern, request.message, re.IGNORECASE) for pattern in INJECTION_PATTERNS):
        return GuardrailResult(action="block", reason="Potenzielle Prompt Injection")
    if decision.confidence < 0.70:
        return GuardrailResult(action="human_review", reason="Confidence unter Automatisierungsschwelle")
    if decision.priority == "high":
        return GuardrailResult(action="human_review", reason="Hohe Priorität benötigt Freigabe")
    return GuardrailResult(action="allow", reason="Policy erfüllt")
