"""Chapter 3 — Testing. See ../TASK.md."""

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


# TODO: script the full successful tool sequence for one ticket, then finish
def happy_path_model() -> FunctionModel:
    return scripted_model(
        finish(f"Ticket {TICKET_ID} skipped — replace with full tool sequence."),
    )


# TODO: script a path that never classifies (so resolve must not happen)
def missing_classify_model() -> FunctionModel:
    return scripted_model(
        finish("done without classify"),
    )


# TODO: run the agent with happy_path_model and assert the ticket ended up correctly resolved
def test_happy_path(mock_helpdesk: MockHelpdeskSDK) -> None:
    pass


# TODO: run with missing_classify_model and assert nothing was resolved
def test_agent_cannot_resolve_without_classify(mock_helpdesk: MockHelpdeskSDK) -> None:
    pass


# TODO: process once, then again; mutating tools should not run a second time
def test_second_run_is_idempotent_when_already_resolved(
    mock_helpdesk: MockHelpdeskSDK,
) -> None:
    pass


# TODO: make resolve fail in the mock and assert the tool wrapper returns an error result
def test_tool_errors_are_returned_as_error_results(
    mock_helpdesk: MockHelpdeskSDK,
) -> None:
    def broken_resolve(ticket_id: int) -> dict[str, object]:
        raise RuntimeError("helpdesk backend unavailable")

    mock_helpdesk.resolve_ticket = broken_resolve  # type: ignore[method-assign]


def main() -> int:
    return pytest.main([str(Path(__file__).resolve()), "-q"])


if __name__ == "__main__":
    raise SystemExit(main())
