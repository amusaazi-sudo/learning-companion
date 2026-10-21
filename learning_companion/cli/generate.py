"""Menu option 1: generate questions with the LLM and review each one."""

from __future__ import annotations

from ..llm_client import LLMError
from ..models import Question
from ..quiz_manager import QuizManager
from .terminal import ask, ask_int, divider, error, info, success, warning


def generate_questions_flow(manager: QuizManager) -> None:
    topic = ask("Enter a topic to generate questions about: ")
    if not topic:
        warning("Topic cannot be empty.")
        return
    num_mcq = ask_int("How many multiple-choice questions? [3]: ", default=3)
    num_freeform = ask_int("How many freeform questions? [2]: ", default=2)

    info(f"\nAsking the LLM for questions about '{topic}'...")
    try:
        candidates = manager.generate_questions(topic, num_mcq, num_freeform)
    except LLMError as exc:
        error(f"LLM request failed: {exc}")
        return

    accepted = 0
    for q in candidates:
        if review_question(q):
            manager.add_question(q)
            accepted += 1
    success(f"\nSaved {accepted}/{len(candidates)} question(s).")


def review_question(q: Question) -> bool:
    """Show one generated question; return True if the user keeps it (edited or not)."""
    divider()
    info(f"[{q.q_type.upper()}] {q.text}")
    if q.is_mcq:
        for i, opt in enumerate(q.options, 1):
            marker = "  <-- correct" if opt == q.correct_answer else ""
            info(f"   {i}. {opt}{marker}")
    else:
        info(f"   Reference answer: {q.correct_answer}")

    choice = ask("Accept (a) / Reject (r) / Edit (e)? [a]: ").lower() or "a"
    if choice == "r":
        return False
    if choice == "e":
        edit_question(q)
    return True


def edit_question(q: Question) -> None:
    q.text = ask(f"New question text [{q.text}]: ") or q.text
    q.correct_answer = ask(f"New correct answer [{q.correct_answer}]: ") or q.correct_answer
    if q.is_mcq:
        new_opts = ask(f"New options, comma-separated [{', '.join(q.options)}]: ")
        if new_opts:
            q.options = [o.strip() for o in new_opts.split(",") if o.strip()]
