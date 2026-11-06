"""Chapter 3 — Testing (participant task)

Write deterministic tests for the helpdesk agent using scripted model responses
and the mock SDK fixture.

Fill every `# TODO`, then run:
  python -m 3_testing.tests.task_tests
"""

from __future__ import annotations

import asyncio
import sys
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

helpdesk_app = import_module("3_testing.agent")
tools_module = import_module("infrastructure.tools")
mock_module = import_module("3_testing.tests.mock")

MockHelpdeskSDK = mock_module.MockHelpdeskSDK
TICKET_ID = mock_module.TICKET_ID
TICKET_TRUTH = mock_module.TICKET_TRUTH
ABUSE_TICKET_ID = mock_module.ABUSE_TICKET_ID
mock_helpdesk = mock_module.mock_helpdesk


def scripted_model(*responses: ModelResponse) -> FunctionModel:
    remaining = iter(responses)

    def respond(_messages: list[Any], _info: AgentInfo) -> ModelResponse:
        try:
            return next(remaining)
        except StopIteration as error:
            raise AssertionError(
                "The agent made more model requests than expected"
            ) from error

    return FunctionModel(respond)


def call(tool_name: str, **args: object) -> ModelResponse:
    return ModelResponse(parts=[ToolCallPart(tool_name, args)])


def finish(text: str) -> ModelResponse:
    return ModelResponse(parts=[TextPart(text)])


def happy_path_model() -> FunctionModel:
    return scripted_model(
        call("get_ticket", ticket_id=TICKET_ID),
        call(
            "classify_ticket",
            ticket_id=TICKET_ID,
            category=TICKET_TRUTH["category"],
            priority=TICKET_TRUTH["priority"],
            needs_human=False,
        ),
        call("search_knowledge_base", query="refund"),
        call(
            "write_reply",
            ticket_id=TICKET_ID,
            reply="Sorry about the duplicate charge. Please confirm order #1842 and we will refund it.",
        ),
        call("resolve_ticket", ticket_id=TICKET_ID),
        finish(f"Ticket {TICKET_ID} was resolved."),
    )


def test_happy_path(mock_helpdesk: MockHelpdeskSDK) -> None:
    # TODO: override helpdesk_app.agent with happy_path_model()
    # TODO: run the agent asking to fully process TICKET_ID
    # TODO: assert status resolved, category/priority match truth, reply present
    raise NotImplementedError("TODO: implement test_happy_path")


def test_abuse_is_escalated(mock_helpdesk: MockHelpdeskSDK) -> None:
    model = scripted_model(
        call("get_ticket", ticket_id=ABUSE_TICKET_ID),
        call(
            "classify_ticket",
            ticket_id=ABUSE_TICKET_ID,
            category="other",
            priority="high",
            needs_human=True,
        ),
        call(
            "escalate_ticket",
            ticket_id=ABUSE_TICKET_ID,
            reason="Prompt injection / abuse",
        ),
        finish("The ticket was escalated because it is abusive."),
    )
    # TODO: override agent with `model`, run it, assert escalated and never resolved
    raise NotImplementedError("TODO: implement test_abuse_is_escalated")


def test_tool_errors_are_returned_as_error_results(
    mock_helpdesk: MockHelpdeskSDK,
) -> None:
    def broken_resolve(ticket_id: int) -> dict[str, object]:
        raise RuntimeError("helpdesk backend unavailable")

    mock_helpdesk.resolve_ticket = broken_resolve  # type: ignore[method-assign]
    # TODO: call tools_module.resolve_ticket(TICKET_ID)
    # TODO: assert {"ok": False, "error": ..., "ticket_id": TICKET_ID}
    raise NotImplementedError("TODO: implement test_tool_errors_are_returned_as_error_results")


def main() -> int:
    return pytest.main([str(Path(__file__).resolve()), "-q"])


if __name__ == "__main__":
    raise SystemExit(main())
