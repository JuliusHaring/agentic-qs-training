import asyncio
import os
from contextlib import contextmanager
from time import perf_counter

from prometheus_client import Counter, Histogram, start_http_server
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior
from tqdm import tqdm

from infrastructure import logistics_sdk
from infrastructure.tools import CUSTOMS_TOOLS, LOGISTICS_TOOLS
from utils.evaluation.mlflow import summarize_and_log
from utils.models import get_chat_model

model = get_chat_model()

SPACE = os.environ.get("PARTICIPANT_NAME", "local")
PROMETHEUS_PORT = int(os.environ.get("PARTICIPANT_METRICS_PORT", "8000"))
PROMETHEUS_STARTED = False

PACKAGE_PROCESSED_TOTAL = Counter(
    "package_processed_total",
    "Total number of packages processed successfully.",
    ["space"],
)
PACKAGE_FAILED_TOTAL = Counter(
    "package_failed_total",
    "Total number of package processing failures.",
    ["space"],
)
AGENT_RUNS_TOTAL = Counter(
    "agent_runs_total",
    "Total number of agent runs by agent name and status.",
    ["space", "agent_name", "status"],
)
TOOL_RUNS_TOTAL = Counter(
    "tool_runs_total",
    "Total number of tool operations by tool name and status.",
    ["space", "tool_name", "status"],
)
AGENT_RUN_DURATION_SECONDS = Histogram(
    "agent_run_duration_seconds",
    "Duration of agent runs by agent name.",
    ["space", "agent_name"],
)
PACKAGE_PROCESS_DURATION_SECONDS = Histogram(
    "package_process_duration_seconds",
    "Duration of end-to-end package processing.",
    ["space"],
)
TOOL_RUN_DURATION_SECONDS = Histogram(
    "tool_run_duration_seconds",
    "Duration of tool operations by tool name.",
    ["space", "tool_name"],
)


class LogisticsHandoff(BaseModel):
    package_id: int
    package_ref: str
    content_description: str
    hs_code: str
    origin_country: str = Field(min_length=2, max_length=2)
    destination_country: str = Field(min_length=2, max_length=2)
    value_amount: float = Field(ge=0)


@contextmanager
def observe_duration(histogram: Histogram, **labels: str):
    start = perf_counter()
    try:
        yield
    finally:
        histogram.labels(space=SPACE, **labels).observe(perf_counter() - start)


@contextmanager
def observe_agent_run(agent_name: str):
    with observe_duration(AGENT_RUN_DURATION_SECONDS, agent_name=agent_name):
        try:
            yield
        except BaseException:
            AGENT_RUNS_TOTAL.labels(
                space=SPACE, agent_name=agent_name, status="error"
            ).inc()
            raise
        else:
            AGENT_RUNS_TOTAL.labels(
                space=SPACE, agent_name=agent_name, status="success"
            ).inc()


@contextmanager
def observe_tool_run(tool_name: str):
    with observe_duration(TOOL_RUN_DURATION_SECONDS, tool_name=tool_name):
        try:
            yield
        except BaseException:
            TOOL_RUNS_TOTAL.labels(
                space=SPACE, tool_name=tool_name, status="error"
            ).inc()
            raise
        else:
            TOOL_RUNS_TOTAL.labels(
                space=SPACE, tool_name=tool_name, status="success"
            ).inc()


def ensure_prometheus_server_started() -> None:
    global PROMETHEUS_STARTED
    if PROMETHEUS_STARTED:
        return
    start_http_server(PROMETHEUS_PORT, addr="0.0.0.0")
    PROMETHEUS_STARTED = True


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
    with observe_agent_run("agent_logistics"):
        return await agent.run(prompt)


async def agent_customs(shipment: LogisticsHandoff):
    prompt = f"""Complete the customs records for {shipment.package_ref} using
the verified logistics handoff:

- Content description: {shipment.content_description}
- Destination country: {shipment.destination_country}
- Customs value: {shipment.value_amount}
- Logistics classification: HS {shipment.hs_code}, origin {shipment.origin_country}

Inspect existing content descriptions and declarations before writing.

Required order of operations:
1. Check whether the content description for {shipment.package_ref} already exists.
2. If it is missing, call the load-content-descriptions tool first to load
   \"{shipment.content_description}\" for {shipment.package_ref}.
3. Only after the content description exists, check whether the customs
   declaration already exists.
4. If the declaration is missing, create it for destination
   {shipment.destination_country} and value {shipment.value_amount}, selecting the
   correct customs-book entry.
5. Do not create duplicates.

Never call the declaration tool before the content description has been loaded.
Return a concise summary."""
    agent = Agent(
        model=model,
        system_prompt=(
            "You are a customs specialist. Complete all missing customs records "
            "for one package. Always inspect existing records first and use "
            "tools for every operation."
        ),
        tools=CUSTOMS_TOOLS,
    )
    with observe_agent_run("agent_customs"):
        return await agent.run(prompt)


async def process_package(package):
    start = perf_counter()
    try:
        logistics_result = await agent_logistics(package)
        shipment = logistics_result.output

        try:
            customs_result = await agent_customs(shipment)
        except UnexpectedModelBehavior as error:
            PACKAGE_FAILED_TOTAL.labels(space=SPACE).inc()
            return {
                "package_ref": shipment.package_ref,
                "classification": {
                    "content_description": shipment.content_description,
                    "hs_code": shipment.hs_code,
                    "origin_country": shipment.origin_country,
                },
                "customs": {
                    "ok": False,
                    "error": str(error),
                    "agent": "agent_customs",
                },
                "freight": {
                    "ok": False,
                    "skipped": True,
                    "reason": "customs agent failed",
                },
            }

        with observe_tool_run("move_to_freight"):
            freight_result = logistics_sdk.move_to_freight([shipment.package_id])

        output = {
            "package_ref": shipment.package_ref,
            "classification": {
                "content_description": shipment.content_description,
                "hs_code": shipment.hs_code,
                "origin_country": shipment.origin_country,
            },
            "customs": customs_result.output,
            "freight": freight_result,
        }
        PACKAGE_PROCESSED_TOTAL.labels(space=SPACE).inc()
        return output
    except BaseException:
        PACKAGE_FAILED_TOTAL.labels(space=SPACE).inc()
        raise
    finally:
        PACKAGE_PROCESS_DURATION_SECONDS.labels(space=SPACE).observe(
            perf_counter() - start
        )


async def main():
    ensure_prometheus_server_started()
    outputs = []
    packages = [
        package
        for package in logistics_sdk.list_packages()
        if package["status"] == "loaded"
    ]
    for package in tqdm(packages, desc="Processing packages"):
        outputs.append(await process_package(package))

    summary = summarize_and_log(
        [package["id"] for package in packages], name="5_observability"
    )
    return {
        "outputs": outputs,
        "summary": summary,
        "prometheus_metrics": f"http://0.0.0.0:{PROMETHEUS_PORT}/metrics",
        "space": SPACE,
    }


if __name__ == "__main__":
    print(asyncio.run(main()))
