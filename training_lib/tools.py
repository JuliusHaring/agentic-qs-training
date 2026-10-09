"""HTTP-Transport und Registry-Basis für validierte Tool-Adapter."""
from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from .domain import ToolContractError
from .ports import Tool, ToolRegistryPort


class HttpTransport:
    def __init__(self, base_url: str, timeout: float = 3.0) -> None:
        self.base_url = base_url
        self.timeout = timeout

    def request(self, method: str, path: str, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
                response = client.request(method, path, json=json_body)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise ToolContractError(f"Tool-Transport fehlgeschlagen: {error}") from error
        if not isinstance(payload, dict):
            raise ToolContractError("Tool-Rückgabe muss ein JSON-Objekt sein")
        return payload


class ValidatedToolRegistry(ToolRegistryPort):
    def __init__(self, tools: list[Tool]) -> None:
        self._tools = {tool.name: tool for tool in tools}
        if len(self._tools) != len(tools):
            raise ValueError("Toolnamen müssen eindeutig sein")

    def execute(self, name: str, arguments: dict[str, Any], roles: set[str]) -> BaseModel:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolContractError(f"Tool nicht registriert: {name}")
        if tool.required_role not in roles:
            raise ToolContractError(f"Fehlende Rolle für Tool {name}: {tool.required_role}")
        validated_input = tool.input_model.model_validate(arguments)
        raw_result = tool.invoke(validated_input)
        return tool.output_model.model_validate(raw_result)

    def schemas(self) -> list[dict[str, Any]]:
        return [
            {"name": tool.name, "description": tool.__doc__ or "", "inputSchema": tool.input_model.model_json_schema()}
            for tool in self._tools.values()
        ]
