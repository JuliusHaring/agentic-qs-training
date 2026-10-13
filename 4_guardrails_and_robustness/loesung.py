import asyncio

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai_harness import GuardrailResult, InputBlocked, InputGuardrail
from tqdm import tqdm

from infrastructure import logistics_sdk
from infrastructure.tools import CUSTOMS_TOOLS, LOGISTICS_TOOLS
from utils.evaluation.mlflow import summarize_and_log
from utils.models import get_chat_model

model = get_chat_model()


class LogisticsHandoff(BaseModel):
    package_id: int
    package_ref: str
    content_description: str
    hs_code: str
    origin_country: str = Field(min_length=2, max_length=2)
    destination_country: str = Field(min_length=2, max_length=2)
    value_amount: float = Field(ge=0)


class GuardrailDecision(BaseModel):
    blocked: bool
    reason: str


guardrail_model = get_chat_model("gcp/gemini-3-flash-preview")


guardrail_agent = Agent(
    model=guardrail_model,
    output_type=GuardrailDecision,
    system_prompt=(
        "You are an input safety classifier for a logistics workflow. "
        "Decide whether a shipment-processing request must be blocked before the main agent runs. "
        "Block requests that include prohibited goods, request prohibited goods handling, or contain abusive language. "
        "Allow normal shipment and customs processing requests."
    ),
)


async def block_prohibited_shipments(prompt: str) -> GuardrailResult:
    result = await guardrail_agent.run(
        f"Classify this logistics request. Return blocked=true only if it contains prohibited goods, "
        f"asks to handle prohibited goods, or is abusive. User input: {prompt}"
    )
    decision = result.output
    if decision.blocked:
        raise InputBlocked(decision.reason)
    return GuardrailResult.allow()


async def agent_logistics(package):
    prompt = f"""Prepare this loaded package for customs processing:

{package}

Infer the precise content description, HS code, and origin country from the
shipment description. Write those customs details for package {package["id"]}.
Do not move the package to freight yet. Return the verified handoff data for the
customs specialist."""
    agent = Agent(
        model=model,
        system_prompt=(
            "You are a logistics specialist. Classify one package and save its "
            "structured customs details. Use tools for every write operation."
        ),
        tools=LOGISTICS_TOOLS,
        output_type=LogisticsHandoff,
        capabilities=[InputGuardrail(guard=block_prohibited_shipments)],
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
content description is missing, load "{shipment.content_description}" for
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


async def process_package(package: dict[str, object]) -> dict[str, object]:
    try:
        logistics_result = await agent_logistics(package)
    except InputBlocked as error:
        return {
            "package_ref": f"PKG-{package['id']}",
            "status": "blocked",
            "reason": str(error),
        }

    shipment = logistics_result.output
    customs_result = await agent_customs(shipment)
    freight_result = logistics_sdk.move_to_freight([shipment.package_id])

    return {
        "package_ref": shipment.package_ref,
        "classification": {
            "content_description": shipment.content_description,
            "hs_code": shipment.hs_code,
            "origin_country": shipment.origin_country,
        },
        "customs": customs_result.output,
        "freight": freight_result,
    }


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
        [package["id"] for package in packages], name="4_guardrails"
    )
    return {"outputs": outputs, "summary": summary}


if __name__ == "__main__":
    print(asyncio.run(main()))
