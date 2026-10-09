"""Aufgabe 6: Teste Agentenpfade und zeichne sie als MLflow-Trace auf."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from unittest.mock import Mock
import mlflow
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training_lib import Customer, SupportAgent, SupportRequest, Ticket, configure_mlflow, evaluate_guardrails


@mlflow.trace(name="tested_agent_workflow", span_type="CHAIN")
def run_traced(request: SupportRequest, tool_client: object) -> dict[str, object]:
    result = SupportAgent().run_structured(request)
    assert result.decision is not None
    policy = evaluate_guardrails(request, result.decision)
    # TODO(AUFGABE 1): Beende block/human_review ohne Tool-Aufruf.
    # Rufe im allow-Pfad get_customer und create_ticket auf.
    return {"status": "TODO"}


def run_tests() -> None:
    fake_tools = Mock()
    fake_tools.call.side_effect = [Customer(name="Max", email="max@example.com", tier="Gold"), Ticket(id=1, customer_id="C123", issue="Meine Rechnung ist falsch", status="open", priority="medium")]
    # TODO(AUFGABE 2): Teste einen erlaubten und einen Injection-Pfad.
    # Prüfe Resultat, Anzahl der Tool-Aufrufe und assert_not_called im Block-Fall.
    print(json.dumps({"status": "TODO", "hint": "Implementiere zwei Agentenpfad-Tests"}))


def main() -> None:
    configure_mlflow()
    with mlflow.start_run(run_name="agent-tests-exercise"):
        run_tests()


if __name__ == "__main__":
    main()
