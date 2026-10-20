"""Persistence helpers: load/save questions as JSON, append results to a text log."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import List

from .models import Question


class QuestionStore:
    """Reads and writes the list of Question objects to a JSON file."""

    def __init__(self, path: str = "data/questions.json"):
        self.path = path
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def load(self) -> List[Question]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            try:
                raw = json.load(f)
            except json.JSONDecodeError:
                return []
        return [Question.from_dict(item) for item in raw]

    def save(self, questions: List[Question]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([q.to_dict() for q in questions], f, indent=2)


class ResultsLog:
    """Appends test-mode results (score + timestamp) to a plain text log file."""

    def __init__(self, path: str = "data/results.txt"):
        self.path = path
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def append_result(self, correct: int, total: int) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{timestamp} - Score: {correct}/{total}\n"
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line)
