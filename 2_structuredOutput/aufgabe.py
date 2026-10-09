"""Block 2 exercise: improve a badly configured PydanticAI agent with typed output."""
from __future__ import annotations

# Motivation:
# Structured Output ist meist der erste große Schritt von einer Demo zu einem
# belastbaren System.
# Ziel ist hier, einen schlecht konfigurierten Agenten in einen typisierten, validierten
# und nachvollziehbaren Service zu überführen.

import json
import sys
from pathlib import Path
from typing import Any

from pydantic_ai import Agent, ModelRetry, RunContext

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import AgentDecision, SupportDependencies, SYSTEM_PROMPT, structured_test_model


class StructuredSupportAgent:
    """Application service wrapping PydanticAI behind a stable project API."""

    def __init__(self, model: Any) -> None:
        # TODO(AUFGABE 1): Verbessere diese schlechte Ausgangskonfiguration.
        # Algorithmus:
        # 1. Erzeuge `Agent(...)` mit `model`.
        # 2. Ergänze die fehlenden zentralen Agent-Parameter für einen stabilen Lauf.
        # 3. Achte besonders auf den typisierten Output-Vertrag dieses Blocks.
        # 4. Vergib einen stabilen Namen und sinnvolle `retries`.
        # 5. Rufe danach `_register_output_validation()` auf.
        self.agent = Agent(model)

    def _register_output_validation(self) -> None:
        # TODO(AUFGABE 2): Ergänze einen output_validator.
        # Algorithmus:
        # 1. Registriere eine Funktion mit `@self.agent.output_validator`.
        # 2. Prüfe, ob `output.priority` auf high steht.
        # 3. Wenn high und `confidence < 0.75`, löse `ModelRetry` aus.
        # 4. Schreibe bei gültigem Output einen Audit-Eintrag in `ctx.deps.audit_log`.
        # 5. Gib den validierten Output zurück.
        pass

    def run(self, message: str, deps: SupportDependencies) -> AgentDecision:
        # TODO(AUFGABE 3): Verbessere die Ausführung.
        # Algorithmus:
        # 1. Rufe `self.agent.run_sync(...)` mit `message` und `deps=deps` auf.
        # 2. Hole aus dem Ergebnis nur `.output`.
        # 3. Gib ausschließlich das `AgentDecision` zurück.
        return self.agent.run_sync(message).output


def main() -> None:
    deps = SupportDependencies(customer_id="C123")
    service = StructuredSupportAgent(structured_test_model(category="technical", priority="high", confidence=0.91))
    output = service.run("Dringend: vollständiger API-Ausfall", deps)
    print(json.dumps({"output": output.model_dump(mode="json"), "audit_log": deps.audit_log}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
