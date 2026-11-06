"""System under test for deterministic helpdesk agent tests."""

from __future__ import annotations

import asyncio
import os

from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from infrastructure.tools import ALL_TOOLS
from utils.models import get_chat_model
from utils.prompts import BASE_SYSTEM_PROMPT


def _get_default_model():
    if os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_ADMIN_KEY"):
        return get_chat_model()
    return TestModel()


model = _get_default_model()

agent = Agent(
    model=model,
    system_prompt=(
        BASE_SYSTEM_PROMPT
        + "\n\nInspect ticket state before acting. Escalate abuse and human cases. "
        "Resolve only after classification and a reply exist."
    ),
    tools=ALL_TOOLS,
)


async def main() -> None:
    result = await agent.run("Process all open support tickets correctly.")
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
