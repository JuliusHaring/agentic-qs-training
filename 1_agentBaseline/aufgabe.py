"""Block 1 exercise: improve an existing fragile raw-output adapter and agent boundary."""
from __future__ import annotations

# Motivation:
# In echten AI-Projekten scheitern erste Versionen oft nicht am Modell selbst,
# sondern an fragilen Verträgen zwischen Freitext und Code.
# Ziel dieser Aufgabe ist, eine schlechte Baseline robuster und diagnostizierbar zu machen.

import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import AgentResponse, BaseSupportAgent, DecisionDecoder, LocalSupportModel, ModelContractError, SupportRequest, SYSTEM_PROMPT, TextModelPort
from training_lib.domain import AgentDecision


class JsonDecisionDecoder(DecisionDecoder):
    """Bad baseline: too permissive and diagnostically weak."""

    def decode(self, raw_output: str) -> AgentDecision:
        # TODO(AUFGABE 1): Verbessere diese schlechte Lösung.
        # Gehe Schritt für Schritt vor:
        # 1. Parse `raw_output` mit `json.loads(...)`.
        # 2. Wenn das Parsing fehlschlägt, wirf `ModelContractError`.
        # 3. Validiere das Ergebnis mit `AgentDecision.model_validate(...)`.
        # 4. Wenn die Validierung fehlschlägt, wirf ebenfalls `ModelContractError`.
        # 5. Gib nur ein gültiges `AgentDecision` zurück.
        try:
            payload = json.loads(raw_output)
        except Exception:
            payload = {}
        return AgentDecision.model_validate(payload)


class RawTextSupportAgent(BaseSupportAgent):
    def __init__(self, model: TextModelPort, decoder: DecisionDecoder) -> None:
        self.model = model
        self.decoder = decoder

    def run(self, request: SupportRequest) -> AgentResponse:
        # TODO(AUFGABE 2): Verbessere die fehlerhafte Laufzeitlogik.
        # Algorithmus:
        # 1. Rufe das Modell mit System Prompt und Nachricht auf.
        # 2. Speichere den rohen Output immer in `raw_output`.
        # 3. Dekodiere den Output mit dem Decoder.
        # 4. Wenn alles erfolgreich ist, gib `status="completed"` zurück.
        # 5. Wenn ein `ModelContractError` entsteht, gib `status="failed"` zurück.
        # 6. Lege im Fehlerfall eine kurze Diagnose in `diagnostics` ab.
        raw_output = self.model.complete(SYSTEM_PROMPT, request.message)
        try:
            decision = self.decoder.decode(raw_output)
            return AgentResponse(request_id=request.request_id, status="completed", decision=decision, raw_output=raw_output)
        except Exception:
            return AgentResponse(request_id=request.request_id, status="completed", raw_output=raw_output)


@dataclass(frozen=True)
class RunSummary:
    total: int
    successful: int
    parse_rate: float
    distinct_raw_outputs: int


def execute_repeatedly(agent: BaseSupportAgent, request: SupportRequest, runs: int) -> tuple[list[AgentResponse], RunSummary]:
    if runs < 1:
        raise ValueError("runs must be positive")
    # TODO(AUFGABE 3): Verbessere die bestehende Auswertung.
    # Algorithmus:
    # 1. Führe `agent.run(request)` genau `runs`-mal aus.
    # 2. Sammle alle `AgentResponse`-Objekte in einer Liste.
    # 3. Zähle, wie oft `status == "completed"` ist.
    # 4. Berechne `parse_rate = successful / total`.
    # 5. Zähle, wie viele unterschiedliche `raw_output`-Werte vorkommen.
    # 6. Gib Responses und `RunSummary` zurück.
    responses = [agent.run(request) for _ in range(runs)]
    summary = RunSummary(total=runs, successful=runs, parse_rate=1.0, distinct_raw_outputs=1)
    return responses, summary


def main() -> None:
    agent = RawTextSupportAgent(LocalSupportModel(seed=17), JsonDecisionDecoder())
    request = SupportRequest(customer_id="C123", message="Dringend: Mein Login funktioniert nicht")
    responses, summary = execute_repeatedly(agent, request, runs=12)
    print(json.dumps({"summary": summary.__dict__, "responses": [item.model_dump(mode="json") for item in responses]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
