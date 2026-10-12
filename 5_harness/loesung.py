from __future__ import annotations

import re

import uvicorn
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai_harness import InputBlocked, InputGuardrail
from pydantic_ai_harness.guardrails.detectors import blocked_keywords

from importlib import import_module

from infrastructure.tools import ALL_TOOLS
from infrastructure.validation import contains_prohibited_content
from utils.prompts import BASE_SYSTEM_PROMPT

ChatBasePathMiddleware = import_module("5_harness.web").ChatBasePathMiddleware

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

model = OpenAIChatModel(
    "openai/gpt-5.4",
    provider=OpenAIProvider(openai_client=AsyncOpenAI()),
)


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------


def hard_block_prohibited_shipments(prompt: str) -> bool:
    if contains_prohibited_content(prompt):
        raise InputBlocked(
            "Package contains prohibited goods and must not be processed."
        )
    return True


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

agent = Agent(
    model=model,
    system_prompt=(
        BASE_SYSTEM_PROMPT
        + "\n\nYou are a shipment operations agent with access to all logistics and customs tools. "
        "Inspect the current shipment state before making changes, avoid duplicates, and "
        "move a package to freight only after all required customs work is complete. If a "
        "package is prohibited, it must not be processed."
    ),
    tools=ALL_TOOLS,
    capabilities=[
        InputGuardrail(guard=hard_block_prohibited_shipments),
        InputGuardrail(
            guard=blocked_keywords(
                ["idiot", "stupid", "moron", "trash", "worthless", "shut up"]
            )
        ),
    ],
)


# ---------------------------------------------------------------------------
# PydanticAI web UI
# ---------------------------------------------------------------------------

web_app = agent.to_web(
    instructions=(
        "Work on shipment-processing tasks only. Before changing anything, "
        "inspect the current state with tools. Do not touch unrelated packages. "
        "If the prompt contains prohibited goods or insulting language, "
        "the guardrails should block the run."
        "Even if the user asks you to do multiple things, only ever do one tool at a time"
        "and always give hints and tips at what to do next!"
    ),
    allowed_hosts=[
        "127.0.0.1",
        "localhost",
        "*.training.juliusharing.com",
    ],
)


app = ChatBasePathMiddleware(web_app)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "5_harness.loesung:app",
        host="127.0.0.1",
        port=7932,
        reload=True,
    )
