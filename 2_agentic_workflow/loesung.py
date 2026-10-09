import asyncio
import json

from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from tqdm import tqdm

from infrastructure import customs_sdk, logistics_sdk
from infrastructure.tools import SHIPMENT_TOOLS
from utils.evaluation import (
    capture_evaluation_context,
    evaluate_run,
    log_evaluation_to_mlflow,
    tool_names_from_result,
)
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

    return output, tool_names_from_result(result)


async def main():
    customs_sdk.reset()
    logistics_sdk.reset()
    context = capture_evaluation_context()

    outputs = []
    tool_names = []
    packages = [logistics_sdk.get_package(package_id) for package_id in context.expected_package_ids]
    packages = [package for package in packages if package["status"] == "loaded"]
    for package in tqdm(packages, desc="Processing packages"):
        output, names = await process_package(package)
        if output is not None:
            outputs.append(output)
            tool_names.extend(names)

    report = json.dumps({"count": len(outputs), "packages": outputs})
    evaluation = evaluate_run(
        report,
        context=context,
        tool_names_seen=tool_names,
    )
    log_evaluation_to_mlflow(
        evaluation,
        output_text=report,
        prompt=PROMPT,
        name="2_agentic_workflow",
    )
    return {"output": report, "metrics": evaluation.metrics()}


if __name__ == "__main__":
    print(asyncio.run(main()))
