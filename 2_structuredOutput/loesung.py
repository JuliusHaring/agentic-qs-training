"""Block 2 solution: a PydanticAI agent with typed output and validators."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.test import TestModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import AgentDecision, SupportDependencies, SYSTEM_PROMPT, structured_test_model


class StructuredSupportAgent:
    """Application service wrapping PydanticAI behind a stable project API."""

    def __init__(self, model: Any) -> None:
        self.agent = Agent(
            model,
            deps_type=SupportDependencies,
            output_type=AgentDecision,
            system_prompt=SYSTEM_PROMPT,
            retries=2,
            name="support_classifier",
        )
        self._register_output_validation()

    def _register_output_validation(self) -> None:
        @self.agent.output_validator
        def business_rules(ctx: RunContext[SupportDependencies], output: AgentDecision) -> AgentDecision:
            if output.priority.value == "high" and output.confidence < 0.75:
                raise ModelRetry("Hohe Priorität erfordert confidence >= 0.75")
            ctx.deps.audit_log.append({"event": "output_validated", "confidence": output.confidence})
            return output

    def run(self, message: str, deps: SupportDependencies) -> AgentDecision:
        return self.agent.run_sync(message, deps=deps).output


def main() -> None:
    deps = SupportDependencies(customer_id="C123")
    service = StructuredSupportAgent(structured_test_model(category="technical", priority="high", confidence=0.91))
    output = service.run("Dringend: vollständiger API-Ausfall", deps)
    print(json.dumps({"output": output.model_dump(mode="json"), "audit_log": deps.audit_log}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
