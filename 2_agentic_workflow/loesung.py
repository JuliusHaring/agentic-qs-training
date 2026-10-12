import asyncio
import json

from pydantic_ai import Agent
from tqdm import tqdm

from infrastructure import logistics_sdk
from infrastructure.tools import CUSTOMS_TOOLS, LOGISTICS_TOOLS
from utils.evaluation.mlflow import summarize_and_log
from utils.models import get_chat_model

model = get_chat_model()


async def agent_logistics(package):
    prompt = f"""Prepare this loaded package for customs processing:

{package}

Infer the precise content description, HS code, and origin country from the
shipment description. Write those customs details for package {package["id"]}.
Do not move the package to freight yet.

Return JSON with the keys package_id, package_ref, content_description, hs_code,
origin_country, destination_country, and value_amount."""
    agent = Agent(
        model=model,
        system_prompt=(
            "You are a logistics specialist. Classify one package and save its "
            "structured customs details. Use tools for every write operation."
        ),
        tools=LOGISTICS_TOOLS,
    )
    return await agent.run(prompt)


async def agent_customs(shipment):
    package_ref = shipment["package_ref"]
    content_description = shipment["content_description"]
    destination_country = shipment["destination_country"]
    value_amount = shipment["value_amount"]
    prompt = f"""Complete the customs records for {package_ref} using the
verified logistics handoff:

- Content description: {content_description}
- Destination country: {destination_country}
- Customs value: {value_amount}
- Logistics classification: HS {shipment["hs_code"]}, origin {shipment["origin_country"]}

Inspect existing content descriptions and declarations before writing. If the
content description is missing, load "{content_description}" for {package_ref}.
If the declaration is missing, create it for destination {destination_country}
and value {value_amount}, selecting the correct customs-book entry. Do not create
duplicates. Return a concise summary."""
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
    shipment = json.loads(logistics_result.output)

    customs_result = await agent_customs(shipment)
    freight_result = logistics_sdk.move_to_freight([shipment["package_id"]])

    return {
        "package_ref": shipment["package_ref"],
        "classification": {
            "content_description": shipment["content_description"],
            "hs_code": shipment["hs_code"],
            "origin_country": shipment["origin_country"],
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
        [package["id"] for package in packages], name="2_agentic_workflow"
    )
    return {"outputs": outputs, "summary": summary}


if __name__ == "__main__":
    print(asyncio.run(main()))
