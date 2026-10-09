"""Aufgabe 1: Führe den Raw-Text-Agenten aus und untersuche seine Grenzen."""
from __future__ import annotations
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training_lib import SupportAgent, SupportRequest, fragile_parse


def observe(agent: SupportAgent, request: SupportRequest, runs: int) -> list[dict[str, object]]:
    observations: list[dict[str, object]] = []
    # TODO(AUFGABE 1): Rufe agent.run_raw(request) mehrfach auf. Speichere Raw Output,
    # Parse-Erfolg und Fehlerart pro Lauf. Nutze fragile_parse bewusst unverändert.
    return observations


def main() -> None:
    request = SupportRequest(customer_id="C123", message="Dringend: Mein Login funktioniert nicht")
    observations = observe(SupportAgent(), request, 6)
    parse_rate = sum(bool(item.get("parseable")) for item in observations) / len(observations) if observations else 0.0
    print(json.dumps({"prompt_only_json_parse_rate": parse_rate, "runs": observations}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
