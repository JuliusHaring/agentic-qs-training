from __future__ import annotations

import mlflow
import uvicorn
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai_harness import InputBlocked, InputGuardrail

from importlib import import_module

from infrastructure.tools import ALL_TOOLS
from utils.models import get_chat_model
from utils.prompts import BASE_SYSTEM_PROMPT
from utils.chat_ui import ChatBasePathMiddleware
from utils.evaluation.mlflow import setup_mlflow

# ---------------------------------------------------------------------------
# MLFlow
# ---------------------------------------------------------------------------

setup_mlflow(autolog=True)

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


model = get_chat_model()


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------


class GuardrailDecision(BaseModel):
    blocked: bool
    reason: str


guardrail_model = get_chat_model("gcp/gemini-3-flash-preview")


guardrail_agent = Agent(
    model=guardrail_model,
    output_type=GuardrailDecision,
    system_prompt=(
        "You are an input safety classifier for a logistics and customs assistant. "
        "Decide whether the user input must be blocked before the main agent runs. "
        "Block inputs that request or include prohibited goods handling, abusive or insulting language, "
        "or clearly switch the conversation to another unrelated topic such as movies, sports, politics, "
        "programming help, medical advice, or other non-logistics domains. "
        "Do not block neutral small talk, greetings, thanks, clarifications, or general conversation that does not try to steer the assistant into another domain. "
        "When in doubt, allow."
    ),
)


async def llm_guardrail(prompt: str) -> bool:
    result = await guardrail_agent.run(
        f"Classify this user input for the shipment assistant. "
        f"Return blocked=true only if it is abusive, asks to handle prohibited goods, or clearly changes the conversation to another domain. "
        f"Allow greetings, acknowledgements, thanks, short social conversation, and clarifying questions. "
        f"User input: {prompt}"
    )
    decision = result.output
    if decision.blocked:
        raise InputBlocked(decision.reason)
    return True

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class MLflowSessionCapability(AbstractCapability[None]):
    """Group all autologged turns of a PydanticAI conversation in one session."""

    async def before_run(self, ctx: RunContext[None]) -> None:
        if ctx.conversation_id:
            mlflow.update_current_trace(session_id=ctx.conversation_id)


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
        MLflowSessionCapability(),
        InputGuardrail(guard=llm_guardrail),
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
        "1_traces_debugging.loesung_chat:app",
        host="127.0.0.1",
        port=7932,
        reload=True,
    )
