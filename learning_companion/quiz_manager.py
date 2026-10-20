"""Core application logic: question selection, practice/test flows, stats.

This module is intentionally free of any direct network calls or `input()`
prompts so that its logic (weighting, selection, evaluation of MCQs, file
persistence) is easy to unit test in isolation. The `LLMClient` is only
instantiated lazily, the first time it's actually needed.
"""

from __future__ import annotations

import random
from typing import List, Optional, Tuple

from .llm_client import LLMClient, LLMError
from .models import Question
from .storage import QuestionStore, ResultsLog


def compute_weight(question: Question) -> float:
    """Higher weight = more likely to be picked in Practice mode.

    Unseen questions get a solid baseline weight so new material gets
    exercised. Seen questions get a weight that grows as their accuracy
    drops, so frequently-missed questions surface more often while
    mastered questions fade into the background (but never disappear
    entirely, since a min weight is always kept).
    """
    if question.times_shown == 0:
        return 3.0
    accuracy = question.times_correct / question.times_shown
    return max(0.5, 3.0 * (1 - accuracy) + 0.5)


def weighted_choice(questions: List[Question]) -> Question:
    """Pick one question at random, weighted by compute_weight."""
    if not questions:
        raise ValueError("No questions to choose from.")
    weights = [compute_weight(q) for q in questions]
    return random.choices(questions, weights=weights, k=1)[0]


class QuizManager:
    """Orchestrates persistence plus the four interactive modes."""

    def __init__(
        self,
        store: Optional[QuestionStore] = None,
        results_log: Optional[ResultsLog] = None,
        llm_client: Optional[LLMClient] = None,
    ):
        self.store = store or QuestionStore()
        self.results_log = results_log or ResultsLog()
        self._llm_client = llm_client  # lazily created so tests don't need an API key
        self.questions: List[Question] = self.store.load()

    # ------------------------------------------------------------------
    @property
    def llm_client(self) -> LLMClient:
        if self._llm_client is None:
            self._llm_client = LLMClient()
        return self._llm_client

    def save(self) -> None:
        self.store.save(self.questions)

    def active_questions(self) -> List[Question]:
        return [q for q in self.questions if q.active]

    def find_by_id(self, qid: str) -> Optional[Question]:
        return next((q for q in self.questions if q.id == qid), None)

    # ---- generation ----------------------------------------------------
    def generate_questions(self, topic: str, num_mcq: int = 3, num_freeform: int = 2) -> List[Question]:
        """Call the LLM and return Question objects (not yet saved)."""
        raw_items = self.llm_client.generate_questions(topic, num_mcq, num_freeform)
        return [
            Question(
                topic=topic,
                text=item["text"],
                q_type=item["q_type"],
                correct_answer=item["correct_answer"],
                options=item["options"],
                source="LLM",
            )
            for item in raw_items
        ]

    def add_question(self, question: Question) -> None:
        self.questions.append(question)
        self.save()

    # ---- management -----------------------------------------------------
    def set_active(self, qid: str, active: bool) -> bool:
        q = self.find_by_id(qid)
        if q is None:
            return False
        q.set_active(active)
        self.save()
        return True

    # ---- evaluation -----------------------------------------------------
    def evaluate_mcq(self, question: Question, chosen_option: str) -> bool:
        return chosen_option.strip().lower() == question.correct_answer.strip().lower()

    def evaluate_freeform(self, question: Question, user_answer: str) -> Tuple[bool, str]:
        """Ask the LLM to judge a freeform answer.

        Deliberately does NOT catch LLMError here: an infrastructure failure
        (network, auth, rate limit) is not evidence the student got the
        question wrong, so it must not be silently converted into an
        incorrect attempt. Callers should catch LLMError themselves and
        decide not to call record_attempt() when it's raised.
        """
        return self.llm_client.evaluate_freeform(
            question.text, question.correct_answer, user_answer
        )

    def record_attempt(self, question: Question, correct: bool) -> None:
        question.record_attempt(correct)
        self.save()

    # ---- practice / test picking ----------------------------------------
    def pick_practice_question(self) -> Question:
        return weighted_choice(self.active_questions())

    def pick_test_questions(self, n: int) -> List[Question]:
        pool = self.active_questions()
        n = max(0, min(n, len(pool)))
        return random.sample(pool, n)

    def log_test_result(self, correct: int, total: int) -> None:
        self.results_log.append_result(correct, total)
