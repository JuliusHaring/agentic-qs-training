"""Block 1 solution: implement the raw-output adapter and agent boundary."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training_lib import AgentResponse, BaseSupportAgent, DecisionDecoder, LocalSupportModel, ModelContractError, SupportRequest, SYSTEM_PROMPT, TextModelPort
from training_lib.domain import AgentDecision


class JsonDecisionDecoder(DecisionDecoder):
    """Strictly decodes raw JSON; markdown or prose is rejected intentionally."""

    def decode(self, raw_output: str) -> AgentDecision:
        try:
            payload = json.loads(raw_output)
        except json.JSONDecodeError as error:
            raise ModelContractError(f"Model did not return plain JSON: {error.msg}") from error
        if not isinstance(payload, dict):
            raise ModelContractError("Top-level model output must be an object")
        try:
            return AgentDecision.model_validate(payload)
        except ValueError as error:
            raise ModelContractError(f"Output violates decision contract: {error}") from error


class RawTextSupportAgent(BaseSupportAgent):
    def __init__(self, model: TextModelPort, decoder: DecisionDecoder) -> None:
        self.model = model
        self.decoder = decoder

    def run(self, request: SupportRequest) -> AgentResponse:
        raw = self.model.complete(SYSTEM_PROMPT, request.message)
        try:
            decision = self.decoder.decode(raw)
            return AgentResponse(request_id=request.request_id, status="completed", raw_output=raw, decision=decision)
        except ModelContractError as error:
            return AgentResponse(request_id=request.request_id, status="failed", raw_output=raw, diagnostics={"stage": "decode", "error": str(error)})


@dataclass(frozen=True)
class RunSummary:
    total: int
    successful: int
    parse_rate: float
    distinct_raw_outputs: int


def execute_repeatedly(agent: BaseSupportAgent, request: SupportRequest, runs: int) -> tuple[list[AgentResponse], RunSummary]:
    if runs < 1:
        raise ValueError("runs must be positive")
    responses = [agent.run(request) for _ in range(runs)]
    successful = sum(response.status == "completed" for response in responses)
    distinct = len({response.raw_output for response in responses})
    return responses, RunSummary(runs, successful, successful / runs, distinct)


def main() -> None:
    agent = RawTextSupportAgent(LocalSupportModel(seed=17), JsonDecisionDecoder())
    request = SupportRequest(customer_id="C123", message="Dringend: Mein Login funktioniert nicht")
    responses, summary = execute_repeatedly(agent, request, runs=12)
    print(json.dumps({"summary": summary.__dict__, "responses": [item.model_dump(mode="json") for item in responses]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
