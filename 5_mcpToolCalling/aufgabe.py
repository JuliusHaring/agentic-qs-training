"""Aufgabe 5: Baue eine validierte MCP-nahe Tool-Kette."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training_lib import SupportAgent, SupportRequest, TOOL_SCHEMAS, ToolClient, evaluate_guardrails


def execute(base_url: str, request: SupportRequest) -> dict[str, object]:
    result = SupportAgent().run_structured(request)
    assert result.decision is not None
    policy = evaluate_guardrails(request, result.decision)
    if policy.action != "allow":
        return {"status": policy.action, "reason": policy.reason}
    tools = ToolClient(base_url)
    # TODO(AUFGABE 1): Rufe in dieser Reihenfolge get_customer, create_ticket und
    # update_ticket_status auf. ToolClient validiert Argumente und Rückgaben.
    # Gib validierte Kunden- und Ticketdaten zurück.
    return {"status": "TODO"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    print(json.dumps({"available_tool_schemas": TOOL_SCHEMAS}, ensure_ascii=False, indent=2))
    print(json.dumps(execute(args.base_url, SupportRequest(customer_id="C123", message="Mein Login funktioniert nicht")), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
