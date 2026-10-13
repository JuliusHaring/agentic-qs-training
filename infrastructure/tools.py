from __future__ import annotations

from typing import Any

from pydantic_ai import Tool

from infrastructure import customs_sdk, logistics_sdk

RecoverableToolError = RuntimeError | ValueError | TypeError | LookupError


def _error_result(error: Exception, **context: object) -> dict[str, object]:
    return {"ok": False, "error": str(error), **context}


def list_packages() -> list[dict[str, object]] | dict[str, object]:
    try:
        return logistics_sdk.list_packages()
    except RecoverableToolError as error:
        return _error_result(error)


def write_customs_details(
    package_id: int,
    content_description: str,
    hs_code: str,
    origin_country: str,
) -> dict[str, object]:
    try:
        return logistics_sdk.write_customs_details(
            package_id,
            content_description,
            hs_code,
            origin_country,
        )
    except RecoverableToolError as error:
        return _error_result(error, package_id=package_id)


def move_to_freight(package_ids: list[int]) -> dict[str, object]:
    try:
        return logistics_sdk.move_to_freight(package_ids)
    except RecoverableToolError as error:
        return _error_result(error, package_ids=package_ids)


def load_content_descriptions(items: list[dict[str, str]]) -> dict[str, object]:
    try:
        return customs_sdk.load_content_descriptions(items)
    except RecoverableToolError as error:
        return _error_result(error)


def list_content_descriptions() -> list[dict[str, str]] | dict[str, object]:
    try:
        return customs_sdk.list_content_descriptions()
    except RecoverableToolError as error:
        return _error_result(error)


def get_customs_book() -> dict[str, Any]:
    try:
        return customs_sdk.get_customs_book()
    except RecoverableToolError as error:
        return _error_result(error)


def get_hs_code_dictionary() -> dict[str, Any]:
    try:
        return customs_sdk.get_hs_code_dictionary()
    except RecoverableToolError as error:
        return _error_result(error)


def create_customs_declaration(
    package_ref: str,
    content_description: str,
    destination_country: str,
    value_amount: float,
    customs_book_entry: str,
) -> dict[str, object]:
    try:
        return customs_sdk.create_customs_declaration(
            package_ref,
            content_description,
            destination_country,
            value_amount,
            customs_book_entry,
        )
    except RecoverableToolError as error:
        return _error_result(error, package_ref=package_ref)


def list_customs_declarations() -> list[dict[str, object]] | dict[str, object]:
    try:
        return customs_sdk.list_customs_declarations()
    except RecoverableToolError as error:
        return _error_result(error)


LIST_PACKAGES_TOOL = Tool(
    list_packages,
    name="list_packages",
    description="List all packages currently known to logistics, including status and customs details.",
)
WRITE_CUSTOMS_DETAILS_TOOL = Tool(
    write_customs_details,
    name="write_customs_details",
    description="Attach customs details to a package in logistics using package_id, content_description, hs_code, and origin_country.",
)
MOVE_TO_FREIGHT_TOOL = Tool(
    move_to_freight,
    name="move_to_freight",
    description="Move packages into freight after all customs work is complete. Input is a list of numeric package IDs.",
)
LOAD_CONTENT_DESCRIPTIONS_TOOL = Tool(
    load_content_descriptions,
    name="load_content_descriptions",
    description="Load missing package content descriptions into customs. Input is a list of items with package_ref and content_description.",
)
LIST_CONTENT_DESCRIPTIONS_TOOL = Tool(
    list_content_descriptions,
    name="list_content_descriptions",
    description="List all package content descriptions currently loaded in customs.",
)
GET_CUSTOMS_BOOK_TOOL = Tool(
    get_customs_book,
    name="get_customs_book",
    description="Get the valid customs book entries for declarations.",
)
GET_HS_CODE_DICTIONARY_TOOL = Tool(
    get_hs_code_dictionary,
    name="get_hs_code_dictionary",
    description="Get HS code classification guidance.",
)
CREATE_CUSTOMS_DECLARATION_TOOL = Tool(
    create_customs_declaration,
    name="create_customs_declaration",
    description="Create one missing customs declaration using package_ref, content_description, destination_country, value_amount, and a valid customs_book_entry.",
)
LIST_CUSTOMS_DECLARATIONS_TOOL = Tool(
    list_customs_declarations,
    name="list_customs_declarations",
    description="List all customs declarations that have already been created.",
)

LOGISTICS_TOOLS = [
    LIST_PACKAGES_TOOL,
    WRITE_CUSTOMS_DETAILS_TOOL,
    MOVE_TO_FREIGHT_TOOL,
]
CUSTOMS_TOOLS = [
    LOAD_CONTENT_DESCRIPTIONS_TOOL,
    LIST_CONTENT_DESCRIPTIONS_TOOL,
    GET_CUSTOMS_BOOK_TOOL,
    GET_HS_CODE_DICTIONARY_TOOL,
    CREATE_CUSTOMS_DECLARATION_TOOL,
    LIST_CUSTOMS_DECLARATIONS_TOOL,
]
ALL_TOOLS = [*LOGISTICS_TOOLS, *CUSTOMS_TOOLS]

__all__ = ["ALL_TOOLS", "CUSTOMS_TOOLS", "LOGISTICS_TOOLS"]
