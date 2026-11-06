"""Chapter 3 — Testing (solution)"""

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
            reply="Sorry about the duplicate charge. Please confirm order #1842.",
        ),
        call("resolve_ticket", ticket_id=TICKET_ID),
        finish(f"Ticket {TICKET_ID} was resolved."),
    )


def missing_classify_model() -> FunctionModel:
    return scripted_model(
        call("get_ticket", ticket_id=TICKET_ID),
        call(
            "write_reply",
            ticket_id=TICKET_ID,
            reply="Skipping classification on purpose.",
        ),
        finish("done without classify"),
    )


def already_resolved_model() -> FunctionModel:
    return scripted_model(
        call("get_ticket", ticket_id=TICKET_ID),
        finish("Ticket already resolved; no changes."),
    )


def test_happy_path(mock_helpdesk: MockHelpdeskSDK) -> None:
    with helpdesk_app.agent.override(model=happy_path_model()):
        result = asyncio.run(
            helpdesk_app.agent.run(f"Fully process ticket {TICKET_ID}.")
        )

    ticket = mock_helpdesk.get_ticket(TICKET_ID)
    assert ticket["status"] == "resolved"
    assert ticket["category"] == TICKET_TRUTH["category"]
    assert ticket["priority"] == TICKET_TRUTH["priority"]
    assert ticket["reply"]
    assert "resolved" in result.output.lower()


def test_agent_cannot_resolve_without_classify(mock_helpdesk: MockHelpdeskSDK) -> None:
    with helpdesk_app.agent.override(model=missing_classify_model()):
        asyncio.run(helpdesk_app.agent.run(f"Process ticket {TICKET_ID}."))

    ticket = mock_helpdesk.get_ticket(TICKET_ID)
    assert ticket["status"] == "open"
    assert mock_helpdesk.call_count("resolve_ticket") == 0
    assert mock_helpdesk.call_count("classify_ticket") == 0


def test_second_run_is_idempotent_when_already_resolved(
    mock_helpdesk: MockHelpdeskSDK,
) -> None:
    with helpdesk_app.agent.override(model=happy_path_model()):
        asyncio.run(helpdesk_app.agent.run(f"Fully process ticket {TICKET_ID}."))

    with helpdesk_app.agent.override(model=already_resolved_model()):
        asyncio.run(
            helpdesk_app.agent.run(f"Fully process ticket {TICKET_ID} again.")
        )

    assert mock_helpdesk.call_count("classify_ticket") == 1
    assert mock_helpdesk.call_count("write_reply") == 1
    assert mock_helpdesk.call_count("resolve_ticket") == 1
    assert mock_helpdesk.get_ticket(TICKET_ID)["status"] == "resolved"


def test_tool_errors_are_returned_as_error_results(
    mock_helpdesk: MockHelpdeskSDK,
) -> None:
    def broken_resolve(ticket_id: int) -> dict[str, object]:
        raise RuntimeError("helpdesk backend unavailable")

    mock_helpdesk.resolve_ticket = broken_resolve  # type: ignore[method-assign]
    result = tools_module.resolve_ticket(TICKET_ID)
    assert result == {
        "ok": False,
        "error": "helpdesk backend unavailable",
        "ticket_id": TICKET_ID,
    }


def main() -> int:
    return pytest.main([str(Path(__file__).resolve()), "-q"])


if __name__ == "__main__":
    raise SystemExit(main())
