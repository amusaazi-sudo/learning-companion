#!/usr/bin/env python3
"""AI-Powered Learning Companion - command line entry point.

Run with:  python main.py
"""

from __future__ import annotations

import sys
from typing import Optional

from rich.console import Console
from rich.markup import escape
from rich.table import Table

from learning_companion import config
from learning_companion.llm_client import LLMError
from learning_companion.models import Question
from learning_companion.quiz_manager import QuizManager
from learning_companion.storage import QuestionStore, ResultsLog


MENU = """
==== AI-Powered Learning Companion ====
1) Generate Questions (LLM)
2) View Statistics
3) Practice Mode
4) Test Mode
5) Manage Questions (Enable/Disable/List)
6) Quit
"""

console = Console()


def build_manager() -> QuizManager:
    store = QuestionStore(config.QUESTIONS_FILE)
    results_log = ResultsLog(config.RESULTS_FILE)
    return QuizManager(store=store, results_log=results_log)


def prompt_int(prompt: str, default: Optional[int] = None) -> int:
    while True:
        raw = input(prompt).strip()
        if not raw and default is not None:
            return default
        try:
            return int(raw)
        except ValueError:
            print("Please enter a whole number.")


# ---------------------------------------------------------------------
def generate_questions_flow(manager: QuizManager) -> None:
    topic = input("Enter a topic to generate questions about: ").strip()
    if not topic:
        print("Topic cannot be empty.")
        return
    num_mcq = prompt_int("How many multiple-choice questions? [3]: ", default=3)
    num_freeform = prompt_int("How many freeform questions? [2]: ", default=2)

    print(f"\nAsking the LLM for questions about '{topic}'...")
    try:
        candidates = manager.generate_questions(topic, num_mcq, num_freeform)
    except LLMError as exc:
        print(f"LLM request failed: {exc}")
        return

    if not candidates:
        print("No questions were generated.")
        return

    accepted = 0
    for q in candidates:
        print("\n" + "-" * 60)
        print(f"[{q.q_type.upper()}] {q.text}")
        if q.is_mcq:
            for i, opt in enumerate(q.options, 1):
                marker = " <-- correct" if opt == q.correct_answer else ""
                print(f"   {i}. {opt}{marker}")
        else:
            print(f"   Reference answer: {q.correct_answer}")

        choice = input("Accept (a) / Reject (r) / Edit (e)? [a]: ").strip().lower() or "a"
        if choice == "r":
            continue
        if choice == "e":
            new_text = input(f"New question text [{q.text}]: ").strip()
            if new_text:
                q.text = new_text
            new_answer = input(f"New correct answer [{q.correct_answer}]: ").strip()
            if new_answer:
                q.correct_answer = new_answer
            if q.is_mcq:
                new_opts = input(
                    f"New options, comma-separated [{', '.join(q.options)}]: "
                ).strip()
                if new_opts:
                    q.options = [o.strip() for o in new_opts.split(",") if o.strip()]
        manager.add_question(q)
        accepted += 1

    print(f"\nSaved {accepted}/{len(candidates)} question(s).")


# ---------------------------------------------------------------------
def view_statistics(manager: QuizManager) -> None:
    if not manager.questions:
        console.print("[yellow]No questions saved yet.[/yellow]")
        return

    table = Table(title="Question Statistics")
    table.add_column("ID", style="dim")
    table.add_column("Active", justify="center")
    table.add_column("Type")
    table.add_column("Source")
    table.add_column("Shown", justify="right")
    table.add_column("Correct %", justify="right")
    table.add_column("Topic")
    table.add_column("Question")

    for q in manager.questions:
        status = "[green]Yes[/green]" if q.active else "[red]No[/red]"

        # Color the score: green = doing well, yellow = so-so, red = needs practice
        if q.times_shown == 0:
            score = "[dim]-[/dim]"
        elif q.correct_percentage >= 70:
            score = f"[green]{q.correct_percentage}%[/green]"
        elif q.correct_percentage >= 40:
            score = f"[yellow]{q.correct_percentage}%[/yellow]"
        else:
            score = f"[red]{q.correct_percentage}%[/red]"

        table.add_row(
            q.id,
            status,
            q.q_type,
            q.source,
            str(q.times_shown),
            score,
            escape(q.topic),
            escape(q.text),
        )

    console.print(table)


# ---------------------------------------------------------------------
def manage_questions_flow(manager: QuizManager) -> None:
    print("\n1) List all questions\n2) Enable/Disable a question by ID")
    choice = input("Choose: ").strip()
    if choice == "1":
        view_statistics(manager)
        return
    if choice != "2":
        print("Invalid choice.")
        return

    qid = input("Enter question ID: ").strip()
    q = manager.find_by_id(qid)
    if q is None:
        print("No question found with that ID.")
        return

    print("\n" + str(q))
    if q.is_mcq:
        print(f"Options: {q.options}")
    print(f"Correct answer: {q.correct_answer}")
    print(f"Currently: {'ENABLED' if q.active else 'DISABLED'}")

    target = not q.active
    verb = "enable" if target else "disable"
    confirm = input(f"Do you want to {verb} this question? (y/n): ").strip().lower()
    if confirm == "y":
        manager.set_active(qid, target)
        print(f"Question {qid} is now {'ENABLED' if target else 'DISABLED'}.")
    else:
        print("No changes made.")


# ---------------------------------------------------------------------
def _ask_question(manager: QuizManager, q: Question) -> bool:
    """Show a question, collect + evaluate the answer. Returns whether it was correct."""
    print("\n" + "-" * 60)
    print(f"Topic: {q.topic}")
    print(f"Q: {q.text}")
    if q.is_mcq:
        for i, opt in enumerate(q.options, 1):
            print(f"   {i}. {opt}")
        raw = input("Your answer (number or text): ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(q.options):
            chosen = q.options[int(raw) - 1]
        else:
            chosen = raw
        correct = manager.evaluate_mcq(q, chosen)
        print("Correct!" if correct else f"Incorrect. Correct answer: {q.correct_answer}")
    else:
        user_answer = input("Your answer: ").strip()
        print("Evaluating your answer with the LLM...")
        try:
            correct, explanation = manager.evaluate_freeform(q, user_answer)
        except LLMError as exc:
            print(f"Could not evaluate your answer via the LLM: {exc}")
            print("This attempt will not be recorded, since it wasn't your answer that failed.")
            return False
        verdict = "Correct!" if correct else "Incorrect."
        print(f"{verdict} {explanation}")
        if not correct:
            print(f"Reference answer: {q.correct_answer}")

    manager.record_attempt(q, correct)
    return correct


def practice_mode(manager: QuizManager) -> None:
    pool = manager.active_questions()
    if not pool:
        print("No active questions available. Generate or enable some first.")
        return
    print("Practice mode - answer 'n' when asked to continue to stop.")
    while True:
        q = manager.pick_practice_question()
        try:
            _ask_question(manager, q)
        except KeyboardInterrupt:
            print("\nEnding practice session.")
            return
        again = input("\nAnother question? (y/n): ").strip().lower()
        if again != "y":
            return


def test_mode(manager: QuizManager) -> None:
    pool = manager.active_questions()
    if not pool:
        print("No active questions available. Generate or enable some first.")
        return
    n = prompt_int(f"How many questions for this test? (max {len(pool)}): ", default=len(pool))
    n = max(1, min(n, len(pool)))
    questions = manager.pick_test_questions(n)

    correct_count = 0
    for i, q in enumerate(questions, 1):
        print(f"\nQuestion {i}/{n}")
        if _ask_question(manager, q):
            correct_count += 1

    print(f"\nTest complete! You answered {correct_count} out of {n} questions correctly.")
    manager.log_test_result(correct_count, n)


# ---------------------------------------------------------------------
def main() -> None:
    manager = build_manager()
    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()
        if choice == "1":
            generate_questions_flow(manager)
        elif choice == "2":
            view_statistics(manager)
        elif choice == "3":
            practice_mode(manager)
        elif choice == "4":
            test_mode(manager)
        elif choice == "5":
            manage_questions_flow(manager)
        elif choice == "6":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice, try again.")


if __name__ == "__main__":
    main()