import asyncio

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai_harness import GuardrailResult, OutputGuardrail, ToolGuardrail
from pydantic_ai_harness.guardrails import ToolCallInfo
from tqdm import tqdm

from infrastructure import customs_sdk, logistics_sdk
from infrastructure.tools import CUSTOMS_TOOLS, LOGISTICS_TOOLS
from utils.mlflow import summarize_and_log
from utils.models import get_chat_model

model = get_chat_model()


class LogisticsHandoff(BaseModel):
    package_id: int
    package_ref: str
    content_description: str = Field(min_length=3)
    hs_code: str = Field(min_length=4)
    origin_country: str = Field(min_length=2, max_length=2)
    destination_country: str = Field(min_length=2, max_length=2)
    value_amount: float = Field(ge=0)
    prohibited_content: bool = False


class PackageResult(BaseModel):
    package_ref: str
    moved_to_freight: bool
    classification: dict[str, object]
    customs: object | None = None
    declaration: dict[str, object] | None = None
    blocked_reason: str | None = None
    freight: dict[str, object] | None = None


def block_prohibited_handoff(shipment: LogisticsHandoff) -> GuardrailResult:
    if shipment.prohibited_content:
        return GuardrailResult.block(
            f"{shipment.package_ref} contains prohibited content and must not move to freight."
        )
    return GuardrailResult.allow()


def allow_customs_tools_only(tool_call: ToolCallInfo) -> GuardrailResult:
    if tool_call.name == "move_to_freight":
        return GuardrailResult.block("Freight move is only allowed after validation in code.")
    return GuardrailResult.allow()


def customs_complete(shipment: LogisticsHandoff) -> tuple[bool, str | None, dict[str, object] | None]:
    descriptions = customs_sdk.list_content_descriptions()
    declarations = customs_sdk.list_customs_declarations()
    description = next(
        (item for item in descriptions if item["package_ref"] == shipment.package_ref), None
    )
    declaration = next(
        (item for item in declarations if item["package_ref"] == shipment.package_ref), None
    )

    if description is None:
        return False, "missing content description", None
    if declaration is None:
        return False, "missing customs declaration", None
    if description["content_description"] != shipment.content_description:
        return False, "content description mismatch", declaration
    if declaration["destination_country"] != shipment.destination_country:
        return False, "destination mismatch", declaration
    if declaration["value_amount"] != shipment.value_amount:
        return False, "value mismatch", declaration

    return True, None, declaration


async def agent_logistics(package):
    prompt = f"""Prepare this loaded package for customs processing:

{package}

Infer the precise content description, HS code, and origin country from the
shipment description. If the shipment indicates prohibited or illegal goods, set
prohibited_content to true and do not write customs details. Otherwise write
those customs details for package {package["id"]}. Do not move the package to
freight yet. Return the verified handoff data for the customs specialist."""
    agent = Agent(
        model=model,
        system_prompt=(
            "You are a logistics specialist. Classify one package and save its "
            "structured customs details. Detect prohibited goods. Use tools for "
            "every write operation."
        ),
        tools=LOGISTICS_TOOLS,
        capabilities=[
            OutputGuardrail(guard=block_prohibited_handoff),
            ToolGuardrail(guard=allow_customs_tools_only),
        ],
        output_type=LogisticsHandoff,
    )
    return await agent.run(prompt)


async def agent_customs(shipment: LogisticsHandoff):
    prompt = f"""Complete the customs records for {shipment.package_ref} using
the verified logistics handoff:

- Content description: {shipment.content_description}
- Destination country: {shipment.destination_country}
- Customs value: {shipment.value_amount}
- Logistics classification: HS {shipment.hs_code}, origin {shipment.origin_country}

Inspect existing content descriptions and declarations before writing. If the
content description is missing, load \"{shipment.content_description}\" for
{shipment.package_ref}. If the declaration is missing, create it for destination
{shipment.destination_country} and value {shipment.value_amount}, selecting the
correct customs-book entry. Do not create duplicates. Return a concise summary."""
    agent = Agent(
        model=model,
        system_prompt=(
            "You are a customs specialist. Complete all missing customs records "
            "for one package. Always inspect existing records first and use "
            "tools for every operation."
        ),
        tools=CUSTOMS_TOOLS,
    )
    return await agent.run(prompt)


async def process_package(package):
    logistics_result = await agent_logistics(package)
    shipment = logistics_result.output

    if shipment.prohibited_content:
        return PackageResult(
            package_ref=shipment.package_ref,
            moved_to_freight=False,
            classification={
                "content_description": shipment.content_description,
                "hs_code": shipment.hs_code,
                "origin_country": shipment.origin_country,
                "prohibited_content": shipment.prohibited_content,
            },
            blocked_reason="prohibited content",
        ).model_dump()

    customs_result = await agent_customs(shipment)
    is_complete, blocked_reason, declaration = customs_complete(shipment)
    freight_result = (
        logistics_sdk.move_to_freight([shipment.package_id]) if is_complete else None
    )

    return PackageResult(
        package_ref=shipment.package_ref,
        moved_to_freight=is_complete,
        classification={
            "content_description": shipment.content_description,
            "hs_code": shipment.hs_code,
            "origin_country": shipment.origin_country,
            "prohibited_content": shipment.prohibited_content,
        },
        customs=customs_result.output,
        declaration=declaration,
        blocked_reason=blocked_reason,
        freight=freight_result,
    ).model_dump()


async def main():
    outputs = []
    packages = [
        package
        for package in logistics_sdk.list_packages()
        if package["status"] == "loaded"
    ]
    for package in tqdm(packages, desc="Processing packages"):
        outputs.append(await process_package(package))

    summary = summarize_and_log(
        [package["id"] for package in packages], name="4_business_validation"
    )
    return {"outputs": outputs, "summary": summary}


if __name__ == "__main__":
    print(asyncio.run(main()))
