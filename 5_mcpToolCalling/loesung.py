"""Block 5 solution: PydanticAI tools with RunContext and validated HTTP contracts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic_ai import Agent, ModelRetry, RunContext

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import AgentDecision, Customer, SupportDependencies, SYSTEM_PROMPT, Ticket, structured_test_model


class ToolEnabledSupportAgent:
    def __init__(self, model: object) -> None:
        self.agent = Agent(model, deps_type=SupportDependencies, output_type=AgentDecision, system_prompt=SYSTEM_PROMPT, retries=2, toolsets=[])
        self._register_tools()

    def _register_tools(self) -> None:
        @self.agent.tool
        def get_customer(ctx: RunContext[SupportDependencies]) -> Customer:
            """Read and validate the customer assigned to the current request."""
            if ctx.deps.transport is None:
                raise ModelRetry("CRM transport is unavailable")
            payload = ctx.deps.transport.request("GET", f"/customer/{ctx.deps.customer_id}")
            customer = Customer.model_validate(payload)
            ctx.deps.audit_log.append({"tool": "get_customer", "customer_id": ctx.deps.customer_id})
            return customer

        @self.agent.tool
        def create_ticket(ctx: RunContext[SupportDependencies], issue: str, priority: str) -> Ticket:
            """Create a validated support ticket for the current customer."""
            if "ticket_writer" not in ctx.deps.actor_roles:
                raise ModelRetry("The actor lacks the ticket_writer role")
            if ctx.deps.transport is None:
                raise ModelRetry("Ticket transport is unavailable")
            normalized_priority = priority if priority in {"low", "medium", "high"} else "medium"
            sanitized_issue = issue if len(issue.strip()) >= 5 else "Bitte Support-Fall anlegen"
            payload = ctx.deps.transport.request(
                "POST",
                "/tickets",
                {"customer_id": ctx.deps.customer_id, "issue": sanitized_issue, "priority": normalized_priority},
            )
            ticket = Ticket.model_validate(payload)
            if ticket.customer_id != ctx.deps.customer_id:
                raise ModelRetry("Tool returned a ticket for another customer")
            ctx.deps.audit_log.append({"tool": "create_ticket", "ticket_id": ticket.id})
            return ticket

    def run_unvalidated(self, message: str, deps: SupportDependencies) -> dict[str, object]:
        """Unsafe baseline: bypasses tool schemas, role checks and response validation."""
        if deps.transport is None:
            raise RuntimeError("transport missing")
        customer = deps.transport.request("GET", f"/customer/{deps.customer_id}")
        ticket = deps.transport.request("POST", "/tickets", {"customer_id": deps.customer_id, "issue": message, "priority": "high"})
        return {"customer": customer, "ticket": ticket}

    def run(self, message: str, deps: SupportDependencies) -> AgentDecision:
        return self.agent.run_sync(message, deps=deps).output


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
