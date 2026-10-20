"""Data models for the AI-Powered Learning Companion."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from typing import List


MCQ = "mcq"
FREEFORM = "freeform"

LLM_SOURCE = "LLM"
MANUAL_SOURCE = "Manual"


@dataclass
class Question:
    """Represents a single study question, either MCQ or freeform."""

    topic: str
    text: str
    q_type: str  # "mcq" or "freeform"
    correct_answer: str
    options: List[str] = field(default_factory=list)
    source: str = LLM_SOURCE
    active: bool = True
    times_shown: int = 0
    times_correct: int = 0
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    # ---- derived properties -------------------------------------------------
    @property
    def correct_percentage(self) -> float:
        """Percentage (0-100) of past attempts answered correctly."""
        if self.times_shown == 0:
            return 0.0
        return round((self.times_correct / self.times_shown) * 100, 1)

    @property
    def is_mcq(self) -> bool:
        return self.q_type == MCQ

    # ---- mutation helpers -----------------------------------------------------
    def record_attempt(self, correct: bool) -> None:
        self.times_shown += 1
        if correct:
            self.times_correct += 1

    def set_active(self, active: bool) -> None:
        self.active = active

    # ---- serialization ----------------------------------------------------
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Question":
        allowed = set(cls.__dataclass_fields__.keys())
        clean = {k: v for k, v in data.items() if k in allowed}
        return cls(**clean)

    def __str__(self) -> str:
        status = "ON" if self.active else "OFF"
        return (
            f"[{self.id}] ({status}) [{self.q_type.upper()}] "
            f"Topic: {self.topic}\n  Q: {self.text}"
        )
