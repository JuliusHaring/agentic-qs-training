"""Block 6 solution: PydanticAI tests with stable fakes, explicit tool order, and MLflow traces."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import mlflow
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import AgentDecision, Customer, SupportDependencies, SYSTEM_PROMPT, Ticket, structured_test_model


class FakeTransport:
    def __init__(self, fail: bool = False, broken_customer: bool = False) -> None:
        self.fail = fail
        self.broken_customer = broken_customer
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def request(self, method: str, path: str, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append((method, path, json_body))
        if self.fail:
            raise TimeoutError("simulated timeout")
        if method == "GET":
            if self.broken_customer:
                return {"name": "Max", "tier": "Gold"}
            return {"name": "Max", "email": "max@example.com", "tier": "Gold"}
        assert json_body is not None
        return {
            "id": 10,
            "customer_id": json_body["customer_id"],
            "issue": json_body["issue"],
            "status": "open",
            "priority": json_body["priority"],
        }


class DeterministicToolModelFactory:
    @staticmethod
    def customer_then_ticket() -> FunctionModel:
        def agent_logic(messages: list[Any], info: Any) -> Any:
            if len(messages) <= 1:
                return info.tool_call("get_customer", {})
            if len(messages) == 3:
                return info.tool_call("create_ticket", {"issue": "Login funktioniert nicht", "priority": "high"})
            return {"category": "technical", "priority": "high", "confidence": 0.91, "justification": "Technischer Vorfall nach CRM-Prüfung."}

        return FunctionModel(agent_logic)

    @staticmethod
    def ticket_without_role() -> FunctionModel:
        def agent_logic(messages: list[Any], info: Any) -> Any:
            if len(messages) <= 1:
                return info.tool_call("create_ticket", {"issue": "Rollenprüfung umgehen", "priority": "high"})
            return {"category": "technical", "priority": "high", "confidence": 0.82, "justification": "Ticket wurde angefragt."}

        return FunctionModel(agent_logic)

    @staticmethod
    def customer_only() -> FunctionModel:
        def agent_logic(messages: list[Any], info: Any) -> Any:
            if len(messages) <= 1:
                return info.tool_call("get_customer", {})
            return {"category": "general", "priority": "low", "confidence": 0.76, "justification": "Nur Kundenprüfung erforderlich."}

        return FunctionModel(agent_logic)


class TestableToolAgent:
    def __init__(self, model: TestModel | FunctionModel) -> None:
        self.agent = Agent(
            model,
            deps_type=SupportDependencies,
            output_type=AgentDecision,
            system_prompt=SYSTEM_PROMPT,
            retries=2,
        )

        @self.agent.tool
        def get_customer(ctx: RunContext[SupportDependencies]) -> Customer:
            if ctx.deps.transport is None:
                raise ModelRetry("transport missing")
            payload = ctx.deps.transport.request("GET", f"/customer/{ctx.deps.customer_id}")
            customer = Customer.model_validate(payload)
            ctx.deps.audit_log.append({"tool": "get_customer", "customer_id": ctx.deps.customer_id})
            return customer

        @self.agent.tool
        def create_ticket(ctx: RunContext[SupportDependencies], issue: str, priority: str) -> Ticket:
            if ctx.deps.transport is None:
                raise ModelRetry("transport missing")
            if "ticket_writer" not in ctx.deps.actor_roles:
                raise PermissionError("ticket_writer required")
            normalized_priority = priority if priority in {"low", "medium", "high"} else "medium"
            payload = ctx.deps.transport.request(
                "POST",
                "/tickets",
                {"customer_id": ctx.deps.customer_id, "issue": issue, "priority": normalized_priority},
            )
            ticket = Ticket.model_validate(payload)
            ctx.deps.audit_log.append({"tool": "create_ticket", "ticket_id": ticket.id})
            return ticket

    @mlflow.trace(name="pydantic_ai_support_run", span_type="AGENT")
    def run(self, message: str, deps: SupportDependencies) -> AgentDecision:
        return self.agent.run_sync(message, deps=deps).output


def run_tests() -> dict[str, int]:
    # Red: ein unkontrollierter TestModel-Lauf kann Tool-Aufrufe unvorhersagbar machen.
    unsafe_transport = FakeTransport()
    unsafe_output = TestableToolAgent(structured_test_model()).run(
        "Erstelle ein Ticket ohne robuste Teststeuerung",
        SupportDependencies(customer_id="C123", actor_roles={"support_agent", "ticket_writer"}, transport=unsafe_transport),
    )
    assert unsafe_output.category.value in {"billing", "technical", "general"}

    # Green: deterministische Tool-Reihenfolge für reproduzierbare Trajectory-Tests.
    transport = FakeTransport()
    deps = SupportDependencies(customer_id="C123", actor_roles={"support_agent", "ticket_writer"}, transport=transport)
    output = TestableToolAgent(DeterministicToolModelFactory.customer_then_ticket()).run(
        "Prüfe den Kunden und erstelle ein Ticket",
        deps,
    )
    assert output.category.value == "technical"
    assert [entry["tool"] for entry in deps.audit_log] == ["get_customer", "create_ticket"]
    assert [call[0] for call in transport.calls] == ["GET", "POST"]

    # Negative Case: Rolle fehlt, Tool darf nicht erfolgreich ausgeführt werden.
    read_only_deps = SupportDependencies(
        customer_id="C123",
        actor_roles={"support_agent"},
        transport=FakeTransport(),
    )
    try:
        TestableToolAgent(DeterministicToolModelFactory.ticket_without_role()).run("Erstelle ein Ticket", read_only_deps)
    except PermissionError:
        pass
    else:
        raise AssertionError("Missing role was not rejected")

    # Failure Case: Timeout aus externem System bleibt sichtbar.
    failing_deps = SupportDependencies(
        customer_id="C123",
        actor_roles={"support_agent", "ticket_writer"},
        transport=FakeTransport(fail=True),
    )
    try:
        TestableToolAgent(DeterministicToolModelFactory.customer_only()).run("Prüfe den Kunden", failing_deps)
    except TimeoutError:
        pass
    else:
        raise AssertionError("Timeout was not observable")

    # Broken response: externes System liefert ungültiges Schema.
    broken_deps = SupportDependencies(
        customer_id="C123",
        actor_roles={"support_agent", "ticket_writer"},
        transport=FakeTransport(broken_customer=True),
    )
    try:
        TestableToolAgent(DeterministicToolModelFactory.customer_only()).run("Prüfe den Kunden", broken_deps)
    except Exception as error:
        if type(error).__name__ not in {"ValidationError", "ToolRetryError", "UnexpectedModelBehavior"}:
            raise
    else:
        raise AssertionError("Broken external response was not observable")

    return {"tests": 5, "passed": 5}


def main() -> None:
    mlflow.set_experiment("ai-automation-training")
    with mlflow.start_run(run_name="pydantic-ai-tests"):
        result = run_tests()
        mlflow.log_metrics({**result, "pass_rate": result["passed"] / result["tests"]})
    print(json.dumps(result))


if __name__ == "__main__":
    main()
