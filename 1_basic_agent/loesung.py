import asyncio

from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from infrastructure import logistics_sdk
from infrastructure.tools import ALL_TOOLS
from utils.evaluation.mlflow import summarize_and_log
from utils.prompts import BASE_SYSTEM_PROMPT

model = OpenAIChatModel(
    "openai/gpt-5.4",
    provider=OpenAIProvider(openai_client=AsyncOpenAI()),
)

agent = Agent(
    model=model,
    system_prompt=BASE_SYSTEM_PROMPT,
    tools=ALL_TOOLS,
)

PROMPT = """Process every package that is currently loaded through customs and move it to freight.

Avoid duplicating records that already exist. When finished, report the package references you processed and their total count."""


async def main():
    package_ids = [
        package["id"]
        for package in logistics_sdk.list_packages()
        if package["status"] == "loaded"
    ]
    result = await agent.run(PROMPT)
    summary = summarize_and_log(package_ids, name="1_basic_agent")
    return {"output": str(result.output), "summary": summary}


if __name__ == "__main__":
    print(asyncio.run(main()))
