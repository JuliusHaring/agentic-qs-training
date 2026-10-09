"""Referenzlösung 2: Structured Output als technische Systemgrenze."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import AgentDecision, SupportAgent, SupportRequest


def validate_business_rules(decision: AgentDecision) -> AgentDecision:
    if decision.priority == "high" and decision.confidence < 0.75:
        raise ValueError("Hohe Priorität erfordert mindestens 0.75 Confidence")
    return decision


def main() -> None:
    agent = SupportAgent()
    requests = [
        SupportRequest(customer_id="C123", message="Dringend: vollständiger API-Ausfall"),
        SupportRequest(customer_id="C456", message="Ich möchte meine Adresse ändern"),
    ]
    for request in requests:
        try:
            result = agent.run_structured(request)
            assert result.decision is not None
            decision = validate_business_rules(result.decision)
            print(json.dumps(decision.model_dump(), ensure_ascii=False))
        except (ValidationError, ValueError) as error:
            print(json.dumps({"status": "rejected", "reason": str(error)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
