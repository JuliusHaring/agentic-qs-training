"""Progressiv erweiterbarer Support-Agent."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .llm import LocalModel, SYSTEM_PROMPT
from .models import AgentDecision, SupportRequest


@dataclass
class AgentResult:
    request: SupportRequest
    raw_output: str | None = None
    decision: AgentDecision | None = None
    actions: list[dict[str, Any]] = field(default_factory=list)


class SupportAgent:
    def __init__(self, model: LocalModel | None = None) -> None:
        self.model = model or LocalModel()

    def run_raw(self, request: SupportRequest) -> AgentResult:
        return AgentResult(
            request=request,
            raw_output=self.model.generate_text(SYSTEM_PROMPT, request.message),
        )

    def run_structured(self, request: SupportRequest) -> AgentResult:
        return AgentResult(request=request, decision=self.model.generate_structured(request.message))


def fragile_parse(raw_output: str) -> AgentDecision:
    """Absichtlich fragiler Parser aus Block 1: nur reines JSON funktioniert."""
    return AgentDecision.model_validate(json.loads(raw_output))
