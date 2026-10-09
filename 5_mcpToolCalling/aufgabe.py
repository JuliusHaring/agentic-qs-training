"""Block 5 exercise: improve an unsafe tool-calling agent with validated HTTP contracts."""
from __future__ import annotations

# Motivation:
# Sobald ein Agent echte Tools und Umsysteme nutzt, wird aus einer Textgenerierung
# ein operativer Workflow mit Seiteneffekten.
# Ziel dieser Aufgabe ist, eine unsichere Tool-Integration zu validieren, zu härten
# und kontrollierbar zu machen.

import argparse
import json
import sys
from pathlib import Path

from pydantic_ai import Agent, ModelRetry, RunContext

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import AgentDecision, Customer, SupportDependencies, SYSTEM_PROMPT, Ticket, structured_test_model


class ToolEnabledSupportAgent:
    def __init__(self, model: object) -> None:
        # TODO(AUFGABE 1): Verbessere die schlechte Agentenkonfiguration.
        # Algorithmus:
        # 1. Erzeuge `Agent(...)` mit `model`.
        # 2. Setze `deps_type=SupportDependencies`.
        # 3. Setze `output_type=AgentDecision`.
        # 4. Setze `system_prompt=SYSTEM_PROMPT`.
        # 5. Konfiguriere sinnvolle `retries`.
        # 6. Rufe anschließend `_register_tools()` auf.
        self.agent = Agent(model, output_type=AgentDecision)

    def _register_tools(self) -> None:
        # TODO(AUFGABE 2): Ergänze ein validiertes `get_customer`-Tool.
        # Algorithmus für `get_customer`:
        # 1. Registriere das Tool mit `@self.agent.tool`.
        # 2. Nutze `RunContext[SupportDependencies]`.
        # 3. Prüfe zuerst, ob `transport` vorhanden ist.
        # 4. Rufe dann das Umsystem per GET auf.
        # 5. Validiere die Response mit `Customer.model_validate(...)`.
        # 6. Schreibe einen Audit-Eintrag.
        #
        # TODO(AUFGABE 3): Ergänze ein validiertes `create_ticket`-Tool.
        # Algorithmus für `create_ticket`:
        # 1. Prüfe die Rolle `ticket_writer`.
        # 2. Prüfe, ob `transport` vorhanden ist.
        # 3. Normalisiere kritische Parameter wie `priority` oder zu kurze `issue`-Texte.
        # 4. Rufe das Umsystem per POST auf.
        # 5. Validiere die Response mit `Ticket.model_validate(...)`.
        # 6. Prüfe die Customer-Isolation und schreibe einen Audit-Eintrag.
        pass

    def run_unvalidated(self, message: str, deps: SupportDependencies) -> dict[str, object]:
        """Unsafe baseline: bypasses tool schemas, role checks and response validation."""
        if deps.transport is None:
            raise RuntimeError("transport missing")
        customer = deps.transport.request("GET", f"/customer/{deps.customer_id}")
        ticket = deps.transport.request("POST", "/tickets", {"customer_id": deps.customer_id, "issue": message, "priority": "high"})
        return {"customer": customer, "ticket": ticket}

    def run(self, message: str, deps: SupportDependencies) -> AgentDecision:
        # TODO(AUFGABE 4): Verbessere den produktiven Pfad.
        # Algorithmus:
        # 1. Rufe `self.agent.run_sync(...)` mit `message` und `deps=deps` auf.
        # 2. Lasse den Agenten dabei dieselben Dependencies für Tools verwenden.
        # 3. Gib nur den validierten `.output` zurück.
        return self.agent.run_sync(message).output


def main() -> None:
    from training_lib import HttpTransport

    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    unsafe_deps = SupportDependencies(customer_id="C123", actor_roles={"support_agent"}, transport=HttpTransport(args.base_url))
    unsafe = ToolEnabledSupportAgent(structured_test_model("technical", "medium", .91)).run_unvalidated("Prüfe den Kunden und erstelle bei Bedarf ein Ticket für den defekten Login.", unsafe_deps)
    safe_deps = SupportDependencies(customer_id="C123", actor_roles={"support_agent", "ticket_writer"}, transport=HttpTransport(args.base_url))
    agent = ToolEnabledSupportAgent(structured_test_model("technical", "medium", .91))
    output = agent.run("Prüfe den Kunden und erstelle bei Bedarf ein Ticket für den defekten Login.", safe_deps)
    print(json.dumps({"before": unsafe, "after": {"output": output.model_dump(mode="json"), "audit": safe_deps.audit_log}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
