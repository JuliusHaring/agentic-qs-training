"""Lokaler Modelladapter: reproduzierbar, aber mit realistischen Ausgabeproblemen."""
from __future__ import annotations

import json
import random

from .models import AgentDecision

SYSTEM_PROMPT = """Klassifiziere die Support-Anfrage.
Antworte als JSON mit category, priority, reason und confidence.
category: billing, technical oder general; priority: low, medium oder high.
"""


def _decision(message: str) -> AgentDecision:
    text = message.lower()
    if any(word in text for word in ("rechnung", "zahlung", "invoice")):
        category = "billing"
    elif any(word in text for word in ("login", "fehler", "api", "ausfall")):
        category = "technical"
    else:
        category = "general"
    high = any(word in text for word in ("dringend", "kritisch", "ausfall"))
    return AgentDecision(
        category=category,
        priority="high" if high else "medium",
        reason="Schlüsselbegriffe der Anfrage bestimmen Kategorie und Priorität.",
        confidence=0.92 if category != "general" else 0.68,
    )


class LocalModel:
    """Simuliert Raw Text und technisch erzwungene strukturierte Ausgaben."""

    def __init__(self, seed: int = 7) -> None:
        self._random = random.Random(seed)

    def generate_text(self, prompt: str, message: str) -> str:
        decision = _decision(message).model_dump()
        rendered = json.dumps(decision, ensure_ascii=False)
        variants = [rendered, f"```json\n{rendered}\n```", f"Ergebnis: {rendered}"]
        return self._random.choice(variants)

    def generate_structured(self, message: str) -> AgentDecision:
        return _decision(message)
