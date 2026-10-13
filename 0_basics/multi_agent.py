import asyncio

from pydantic import BaseModel, Field
from pydantic_ai import Agent
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


async def process_package(package):
    logistics_result = await agent_logistics(package)
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
        [package["id"] for package in packages], name="3_structured_output"
    )
    return {"outputs": outputs, "summary": summary}


if __name__ == "__main__":
    print(asyncio.run(main()))
