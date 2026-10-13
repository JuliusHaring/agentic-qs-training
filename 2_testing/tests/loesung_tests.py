from __future__ import annotations

import asyncio
from importlib import import_module
from pathlib import Path
import sys
from typing import Any

import pytest
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.test import TestModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

shipment_app = import_module("2_testing.multi_agent")
tools_module = import_module("infrastructure.tools")
mock_module = import_module("2_testing.tests.mock")

MockSDKs = mock_module.MockSDKs
PACKAGE_ID = mock_module.PACKAGE_ID
PACKAGE_REF = mock_module.PACKAGE_REF
PACKAGE_TRUTH = mock_module.PACKAGE_TRUTH
PROHIBITED_PACKAGE_ID = mock_module.PROHIBITED_PACKAGE_ID
mock_sdks = mock_module.mock_sdks


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


def allow_guardrail() -> TestModel:
    return TestModel(custom_output_args={"blocked": False, "reason": "shipment task"})


def full_processing_model() -> FunctionModel:
    return scripted_model(
        call("list_packages"),
        call("list_content_descriptions"),
        call("list_customs_declarations"),
        call("get_hs_code_dictionary"),
        call("get_customs_book"),
        call(
            "write_customs_details",
            package_id=PACKAGE_ID,
            content_description=PACKAGE_TRUTH["content_description"],
            hs_code=PACKAGE_TRUTH["hs_code"],
            origin_country=PACKAGE_TRUTH["origin_country"],
        ),
        call(
            "load_content_descriptions",
            items=[
                {
                    "package_ref": PACKAGE_REF,
                    "content_description": PACKAGE_TRUTH["content_description"],
                }
            ],
        ),
        call(
            "create_customs_declaration",
            package_ref=PACKAGE_REF,
            content_description=PACKAGE_TRUTH["content_description"],
            destination_country=PACKAGE_TRUTH["destination_country"],
            value_amount=PACKAGE_TRUTH["declared_value"],
            customs_book_entry=PACKAGE_TRUTH["customs_book_entry"],
        ),
        call("move_to_freight", package_ids=[PACKAGE_ID]),
        finish(f"{PACKAGE_REF} was processed and moved to freight."),
    )


def test_happy_path(mock_sdks: MockSDKs) -> None:
    with (
        shipment_app.guardrail_agent.override(model=allow_guardrail()),
        shipment_app.agent.override(model=full_processing_model()),
    ):
        result = asyncio.run(
            shipment_app.agent.run(f"Fully process package {PACKAGE_ID}.")
        )

    package = mock_sdks.logistics.get_package(PACKAGE_ID)
    assert package["status"] == "in_freight"
    assert package["customs_details"] == {
        "content_description": PACKAGE_TRUTH["content_description"],
        "hs_code": PACKAGE_TRUTH["hs_code"],
        "origin_country": PACKAGE_TRUTH["origin_country"],
    }
    assert len(mock_sdks.customs.declarations) == 1
    assert mock_sdks.customs.declarations[0]["package_ref"] == PACKAGE_REF
    assert "moved to freight" in result.output


def test_prohibited_shipment(mock_sdks: MockSDKs) -> None:
    model = scripted_model(
        call("list_packages"),
        finish("The shipment is prohibited and was not processed."),
    )
    with (
        shipment_app.guardrail_agent.override(model=allow_guardrail()),
        shipment_app.agent.override(model=model),
    ):
        result = asyncio.run(
            shipment_app.agent.run(
                f"Inspect and process package {PROHIBITED_PACKAGE_ID}."
            )
        )

    package = mock_sdks.logistics.get_package(PROHIBITED_PACKAGE_ID)
    assert package["status"] == "loaded"
    assert package["customs_details"] is None
    assert mock_sdks.logistics.call_count("write_customs_details") == 0
    assert mock_sdks.logistics.call_count("move_to_freight") == 0
    assert mock_sdks.customs.call_count("create_customs_declaration") == 0
    assert "prohibited" in result.output.lower()


def test_repeated_execution_is_idempotent(mock_sdks: MockSDKs) -> None:
    with (
        shipment_app.guardrail_agent.override(model=allow_guardrail()),
        shipment_app.agent.override(model=full_processing_model()),
    ):
        asyncio.run(shipment_app.agent.run(f"Fully process package {PACKAGE_ID}."))

    first_package = mock_sdks.logistics.get_package(PACKAGE_ID)
    first_declarations = list(mock_sdks.customs.declarations)
    first_descriptions = dict(mock_sdks.customs.descriptions)

    repeat_model = scripted_model(
        call("list_packages"),
        call("list_content_descriptions"),
        call("list_customs_declarations"),
        finish("The shipment is already fully processed; no changes were made."),
    )
    with (
        shipment_app.guardrail_agent.override(model=allow_guardrail()),
        shipment_app.agent.override(model=repeat_model),
    ):
        result = asyncio.run(
            shipment_app.agent.run(f"Fully process package {PACKAGE_ID} again.")
        )

    assert mock_sdks.logistics.get_package(PACKAGE_ID) == first_package
    assert mock_sdks.customs.declarations == first_declarations
    assert mock_sdks.customs.descriptions == first_descriptions
    assert mock_sdks.logistics.call_count("write_customs_details") == 1
    assert mock_sdks.logistics.call_count("move_to_freight") == 1
    assert mock_sdks.customs.call_count("create_customs_declaration") == 1
    assert "no changes" in result.output.lower()


def test_failure_during_execution(mock_sdks: MockSDKs) -> None:
    mock_sdks.customs.fail_declaration = True
    model = scripted_model(
        call("list_packages"),
        call(
            "write_customs_details",
            package_id=PACKAGE_ID,
            content_description=PACKAGE_TRUTH["content_description"],
            hs_code=PACKAGE_TRUTH["hs_code"],
            origin_country=PACKAGE_TRUTH["origin_country"],
        ),
        call(
            "load_content_descriptions",
            items=[
                {
                    "package_ref": PACKAGE_REF,
                    "content_description": PACKAGE_TRUTH["content_description"],
                }
            ],
        ),
        call(
            "create_customs_declaration",
            package_ref=PACKAGE_REF,
            content_description=PACKAGE_TRUTH["content_description"],
            destination_country=PACKAGE_TRUTH["destination_country"],
            value_amount=PACKAGE_TRUTH["declared_value"],
            customs_book_entry=PACKAGE_TRUTH["customs_book_entry"],
        ),
        finish("Customs failed, so the shipment was not moved to freight."),
    )
    with (
        shipment_app.guardrail_agent.override(model=allow_guardrail()),
        shipment_app.agent.override(model=model),
    ):
        result = asyncio.run(
            shipment_app.agent.run(f"Fully process package {PACKAGE_ID}.")
        )

    assert mock_sdks.logistics.get_package(PACKAGE_ID)["status"] == "customs_ready"
    assert mock_sdks.customs.declarations == []
    assert mock_sdks.logistics.call_count("move_to_freight") == 0
    assert "not moved" in result.output.lower()


def test_external_logistics_tool_errors_are_returned_as_error_results(
    mock_sdks: MockSDKs,
) -> None:
    original_write = mock_sdks.logistics.write_customs_details

    def broken_write(
        package_id: int,
        content_description: str,
        hs_code: str,
        origin_country: str,
    ) -> dict[str, object]:
        raise RuntimeError("logistics backend unavailable")

    mock_sdks.logistics.write_customs_details = broken_write  # type: ignore[method-assign]
    result = tools_module.write_customs_details(
        PACKAGE_ID,
        str(PACKAGE_TRUTH["content_description"]),
        str(PACKAGE_TRUTH["hs_code"]),
        str(PACKAGE_TRUTH["origin_country"]),
    )

    assert result == {
        "ok": False,
        "error": "logistics backend unavailable",
        "package_id": PACKAGE_ID,
    }
    assert mock_sdks.logistics.get_package(PACKAGE_ID)["customs_details"] is None

    mock_sdks.logistics.write_customs_details = original_write  # type: ignore[method-assign]


def test_external_customs_tool_errors_are_returned_as_error_results(
    mock_sdks: MockSDKs,
) -> None:
    original_create = mock_sdks.customs.create_customs_declaration

    def broken_create(
        package_ref: str,
        content_description: str,
        destination_country: str,
        value_amount: float,
        customs_book_entry: str,
    ) -> dict[str, object]:
        raise RuntimeError("customs backend unavailable")

    mock_sdks.customs.create_customs_declaration = broken_create  # type: ignore[method-assign]
    result = tools_module.create_customs_declaration(
        PACKAGE_REF,
        str(PACKAGE_TRUTH["content_description"]),
        str(PACKAGE_TRUTH["destination_country"]),
        float(PACKAGE_TRUTH["declared_value"]),
        str(PACKAGE_TRUTH["customs_book_entry"]),
    )

    assert result == {
        "ok": False,
        "error": "customs backend unavailable",
        "package_ref": PACKAGE_REF,
    }
    assert mock_sdks.customs.declarations == []

    mock_sdks.customs.create_customs_declaration = original_create  # type: ignore[method-assign]


def main() -> int:
    """Run this test module directly without requiring a pytest CLI command."""
    return pytest.main([str(Path(__file__).resolve()), "-q"])


if __name__ == "__main__":
    raise SystemExit(main())
