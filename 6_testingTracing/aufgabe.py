"""Block 6 exercise: improve a weak test setup with fakes, path assertions, and MLflow traces."""
from __future__ import annotations

# Motivation:
# AI-Workflows testet man nicht nur auf richtigen Output, sondern auf Verhalten unter
# wechselnden Bedingungen, Fehlern und Reaktionen von Umsystemen.
# Ziel dieser Aufgabe ist, aus einer schwachen Test-Baseline eine belastbare Teststrategie
# mit Fakes, Edge Cases und Tracing zu machen.

import json
import sys
from pathlib import Path

import mlflow
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import AgentDecision, Customer, SupportDependencies, SYSTEM_PROMPT, Ticket, structured_test_model


class FakeTransport:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, str, dict | None]] = []

    def request(self, method: str, path: str, json_body: dict | None = None) -> dict:
        # TODO(AUFGABE 1): Verbessere den Fake.
        # Algorithmus:
        # 1. Speichere jeden Request in `self.calls`.
        # 2. Wenn `self.fail` aktiv ist, wirf `TimeoutError`.
        # 3. Wenn `method == "GET"`, gib eine gültige Customer-Response zurück.
        # 4. Wenn `method == "POST"`, gib eine gültige Ticket-Response zurück.
        # 5. Optional: baue einen Modus für kaputte Responses ein, um Edge Cases zu testen.
        return {}


class TestableToolAgent:
    def __init__(self, model: TestModel) -> None:
        # TODO(AUFGABE 2): Verbessere die Test-Baseline.
        # Algorithmus:
        # 1. Erzeuge `Agent(...)` mit `deps_type=SupportDependencies`, `output_type=AgentDecision`
        #    und `system_prompt=SYSTEM_PROMPT`.
        # 2. Registriere `get_customer` als Tool.
        # 3. Registriere `create_ticket` als Tool.
        # 4. Prüfe im Ticket-Tool die Rolle `ticket_writer`.
        # 5. Validiere beide Tool-Responses mit Pydantic-Modellen.
        self.agent = Agent(model, output_type=AgentDecision)

    @mlflow.trace(name="pydantic_ai_support_run", span_type="AGENT")
    def run(self, message: str, deps: SupportDependencies) -> AgentDecision:
        # TODO(AUFGABE 3): Nutze Dependencies sauber und mache den Lauf tracebar.
        # Algorithmus:
        # 1. Rufe `self.agent.run_sync(...)` mit `message` und `deps=deps` auf.
        # 2. Gib nur den `.output` zurück.
        # 3. Belasse die `@mlflow.trace`-Dekoration auf der Methode.
        return self.agent.run_sync(message).output


def run_tests() -> dict[str, int]:
    # TODO(AUFGABE 4): Schreibe explizit mehrere Tests gegen die bestehende schlechte Lösung.
    # Algorithmus:
    # 1. Schreibe einen E2E-/Happy-Path-Test: Agent ausführen, Output prüfen.
    # 2. Prüfe im selben oder in einem zweiten Test die Tool-Reihenfolge über `transport.calls`.
    # 3. Schreibe einen Negativtest ohne `ticket_writer`-Rolle. Erwartung: Fehler oder Ablehnung.
    # 4. Schreibe einen Test mit `FakeTransport(fail=True)`. Erwartung: Timeout wird sichtbar.
    # 5. Schreibe einen Test für eine kaputte Umsystem-Response. Erwartung: Validierung schlägt fehl.
    # 6. Optional: definiere 2-3 stabile Golden-Set-Fälle und prüfe, ob der Agent in allen Fällen
    #    den erwarteten Pfad bzw. die erwartete Kategorie liefert.
    # 7. Zähle am Ende, wie viele Tests geschrieben und bestanden wurden, und gib das als Dict zurück.
    raise NotImplementedError


def main() -> None:
    mlflow.set_experiment("ai-automation-training")
    with mlflow.start_run(run_name="pydantic-ai-tests"):
        result = run_tests()
        mlflow.log_metrics({**result, "pass_rate": result["passed"] / result["tests"]})
    print(json.dumps(result))


if __name__ == "__main__":
    main()
