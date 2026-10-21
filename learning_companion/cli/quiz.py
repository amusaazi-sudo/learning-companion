"""Menu options 3 and 4: Practice mode and Test mode."""

from __future__ import annotations

from ..llm_client import LLMError
from ..models import Question
from ..quiz_manager import QuizManager
from .terminal import ask, ask_int, divider, error, info, success, warning


def practice_mode(manager: QuizManager) -> None:
    if not manager.active_questions():
        warning("No active questions available. Generate or enable some first.")
        return
    info("Practice mode - answer 'n' when asked to continue to stop.")
    while True:
        try:
            ask_question(manager, manager.pick_practice_question())
        except KeyboardInterrupt:
            info("\nEnding practice session.")
            return
        if ask("\nAnother question? (y/n): ").lower() != "y":
            return


def test_mode(manager: QuizManager) -> None:
    pool = manager.active_questions()
    if not pool:
        warning("No active questions available. Generate or enable some first.")
        return
    n = ask_int(f"How many questions for this test? (max {len(pool)}): ", default=len(pool))
    n = max(1, min(n, len(pool)))

    correct_count = 0
    for i, q in enumerate(manager.pick_test_questions(n), 1):
        info(f"\nQuestion {i}/{n}")
        if ask_question(manager, q):
            correct_count += 1

    success(f"\nTest complete! You answered {correct_count} out of {n} questions correctly.")
    manager.log_test_result(correct_count, n)


def ask_question(manager: QuizManager, q: Question) -> bool:
    """Show a question, collect and grade the answer. Returns whether it was correct."""
    divider()
    info(f"Topic: {q.topic}")
    info(f"Q: {q.text}")
    try:
        correct = grade_mcq(manager, q) if q.is_mcq else grade_freeform(manager, q)
    except LLMError as exc:
        error(f"Could not grade your answer: {exc}")
        warning("This attempt was not recorded, since your answer wasn't what failed.")
        return False
    manager.record_attempt(q, correct)
    return correct


def grade_mcq(manager: QuizManager, q: Question) -> bool:
    for i, opt in enumerate(q.options, 1):
        info(f"   {i}. {opt}")
    raw = ask("Your answer (number or text): ")
    chosen = q.options[int(raw) - 1] if raw.isdigit() and 1 <= int(raw) <= len(q.options) else raw
    correct = manager.evaluate_mcq(q, chosen)
    if correct:
        success("Correct!")
    else:
        error(f"Incorrect. Correct answer: {q.correct_answer}")
    return correct


def grade_freeform(manager: QuizManager, q: Question) -> bool:
    answer = ask("Your answer: ")
    info("Evaluating your answer with the LLM...")
    correct, explanation = manager.evaluate_freeform(q, answer)
    if correct:
        success(f"Correct! {explanation}")
    else:
        error(f"Incorrect. {explanation}")
        info(f"Reference answer: {q.correct_answer}")
    return correct
