"""Referenzlösung 1: Basalen Raw-Text-Agenten ausführen und beobachten."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import SupportAgent, SupportRequest, fragile_parse


def main() -> None:
    agent = SupportAgent()
    request = SupportRequest(customer_id="C123", message="Dringend: Mein Login funktioniert nicht")
    observations: list[dict[str, object]] = []

    for run_number in range(1, 7):
        result = agent.run_raw(request)
        assert result.raw_output is not None
        try:
            decision = fragile_parse(result.raw_output)
            observations.append({"run": run_number, "parseable": True, "decision": decision.model_dump()})
        except (json.JSONDecodeError, ValueError) as error:
            observations.append({"run": run_number, "parseable": False, "error": type(error).__name__, "raw": result.raw_output})

    parse_rate = sum(bool(item["parseable"]) for item in observations) / len(observations)
    print(json.dumps({"prompt_only_json_parse_rate": parse_rate, "runs": observations}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
