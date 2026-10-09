import asyncio
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

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

PROMPT = """Process every package that is currently loaded through customs and move it to freight.

Avoid duplicating records that already exist. When finished, report the package references you processed and their total count."""


async def main():
    customs_sdk.reset()
    logistics_sdk.reset()
    context = capture_evaluation_context()

    result = await agent.run(PROMPT)
    output = str(result.output)
    evaluation = evaluate_run(
        output,
        context=context,
        tool_names_seen=tool_names_from_result(result),
    )
    log_evaluation_to_mlflow(
        evaluation,
        output_text=output,
        prompt=PROMPT,
        name="1_basic_agent",
    )
    return {"output": output, "metrics": evaluation.metrics()}


if __name__ == "__main__":
    print(asyncio.run(main()))
