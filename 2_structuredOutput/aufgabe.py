"""Aufgabe 2: Ersetze die JSON-Anweisung durch Structured Output."""
from __future__ import annotations
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training_lib import AgentDecision, SupportAgent, SupportRequest


def validate_business_rules(decision: AgentDecision) -> AgentDecision:
    # TODO(AUFGABE 1): Lehne high bei confidence < 0.75 mit ValueError ab.
    return decision


def classify(agent: SupportAgent, request: SupportRequest) -> AgentDecision | None:
    # TODO(AUFGABE 2): Nutze run_structured, prüfe decision auf None und wende
    # validate_business_rules an. Fange erwartbare Validierungsfehler in main ab.
    return None


def main() -> None:
    agent = SupportAgent()
    for message in ("Dringend: vollständiger API-Ausfall", "Ich möchte meine Adresse ändern"):
        try:
            decision = classify(agent, SupportRequest(customer_id="C123", message=message))
            print(json.dumps(decision.model_dump() if decision else {"status": "TODO"}, ensure_ascii=False))
        except ValueError as error:
            print(json.dumps({"status": "rejected", "reason": str(error)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
