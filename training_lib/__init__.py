"""Shared production-oriented building blocks for the AI automation workshop."""
from .domain import AgentDecision, AgentError, AgentResponse, Category, Customer, GuardrailViolation, ModelContractError, Priority, SupportRequest, Ticket, ToolContractError
from .evaluation import GOLDEN_CASES, EvaluationCase, METRIC_LIBRARY
from .policies import GuardrailPipeline
from .ports import DecisionDecoder, Guardrail, PolicyDecision, TelemetryPort, TextModelPort, Tool, ToolRegistryPort
from .runtime import BaseSupportAgent
from .production import ProductionEvent, QualityGate
from .providers import LocalSupportModel, SYSTEM_PROMPT
from .pydantic_agents import SupportDependencies, create_decision_agent, structured_test_model
from .telemetry import InMemoryTelemetry, MlflowTelemetry
from .tools import HttpTransport, ValidatedToolRegistry

__all__ = [name for name in globals() if not name.startswith("_")]
