"""Menu option 5: list questions or enable/disable one by ID."""

from __future__ import annotations

from ..quiz_manager import QuizManager
from .stats import view_statistics
from .terminal import ask, error, info, success, warning


def manage_questions_flow(manager: QuizManager) -> None:
    info("\n1) List all questions\n2) Enable/Disable a question by ID")
    choice = ask("Choose: ")
    if choice == "1":
        view_statistics(manager)
    elif choice == "2":
        toggle_question(manager)
    else:
        warning("Invalid choice.")


def toggle_question(manager: QuizManager) -> None:
    qid = ask("Enter question ID: ")
    q = manager.find_by_id(qid)
    if q is None:
        error("No question found with that ID.")
        return

    info("\n" + str(q))
    if q.is_mcq:
        info(f"Options: {', '.join(q.options)}")
    info(f"Correct answer: {q.correct_answer}")
    info(f"Currently: {'ENABLED' if q.active else 'DISABLED'}")

    target = not q.active
    verb = "enable" if target else "disable"
    if ask(f"Do you want to {verb} this question? (y/n): ").lower() == "y":
        manager.set_active(qid, target)
        success(f"Question {qid} is now {'ENABLED' if target else 'DISABLED'}.")
    else:
        info("No changes made.")
