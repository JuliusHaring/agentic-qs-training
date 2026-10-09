"""Lokale Modelladapter für reproduzierbare Übungen ohne externen API-Key."""
from __future__ import annotations

import json
import random
from typing import TypeVar

from pydantic import BaseModel

from .domain import AgentDecision, Category, Priority
from .ports import StructuredModelPort

T = TypeVar("T", bound=BaseModel)

SYSTEM_PROMPT = """Du klassifizierst Support-Anfragen.
Gib JSON mit category, priority, reason und confidence zurück.
Erlaubte Kategorien: billing, technical, general.
Erlaubte Prioritäten: low, medium, high.
confidence liegt zwischen 0 und 1.
"""


class LocalSupportModel(StructuredModelPort):
    """Simuliert Formatabweichungen und eine leicht fehlkalibrierte Confidence."""

    def __init__(self, seed: int = 17) -> None:
        self._random = random.Random(seed)

    def _classify(self, message: str) -> AgentDecision:
        normalized = message.lower()
        if any(term in normalized for term in ("rechnung", "zahlung", "invoice")):
            category = Category.BILLING
        elif any(term in normalized for term in ("login", "fehler", "api", "ausfall")):
            category = Category.TECHNICAL
        else:
            category = Category.GENERAL
        urgent = any(term in normalized for term in ("dringend", "kritisch", "ausfall"))
        return AgentDecision(
            category=category,
            priority=Priority.HIGH if urgent else Priority.MEDIUM,
            reason="Die erkannten Schlüsselbegriffe bestimmen Kategorie und Priorität.",
            confidence=0.91 if category != Category.GENERAL else 0.73,
        )

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        payload = json.dumps(self._classify(user_prompt).model_dump(mode="json"), ensure_ascii=False)
        return self._random.choice((payload, f"```json\n{payload}\n```", f"Hier ist die Analyse:\n{payload}"))

    def complete_structured(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T:
        payload = self._classify(user_prompt).model_dump(mode="json")
        return schema.model_validate(payload)
