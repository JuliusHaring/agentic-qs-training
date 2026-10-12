import asyncio
import json

from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from tqdm import tqdm

from infrastructure import customs_sdk, logistics_sdk
from infrastructure.tools import SHIPMENT_TOOLS
from utils.prompts import BASE_SYSTEM_PROMPT

model = OpenAIChatModel(
    "openai/gpt-5.4",
    provider=OpenAIProvider(openai_client=AsyncOpenAI()),
)

agent = Agent(
    model=model,
    system_prompt=BASE_SYSTEM_PROMPT,
    tools=SHIPMENT_TOOLS,
)

PROMPT = """Process package PKG-{package_id} through every missing customs step and move it to freight.

Inspect existing logistics and customs records first and do not create duplicates.
Return JSON with package_ref and processed true / false."""


async def process_package(package):
    package_id = package["id"]
    result = await agent.run(PROMPT.format(package_id=package_id))
    output = json.loads(str(result.output))

    if output != {"package_ref": f"PKG-{package_id}", "processed": True}:
        raise ValueError(f"Unexpected agent output for PKG-{package_id}: {output!r}")

    return output


async def run():
    outputs = []
    packages = [
        package
        for package in logistics_sdk.list_packages()
        if package["status"] == "loaded"
    ]
    for package in tqdm(packages, desc="Processing packages"):
        output = await process_package(package)
        if output is not None:
            outputs.append(output)

    return json.dumps({"count": len(outputs), "packages": outputs})


async def main():
    return await run()


if __name__ == "__main__":
    print(asyncio.run(main()))
