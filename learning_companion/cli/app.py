"""Menu loop that wires every feature to one shared QuizManager."""

from __future__ import annotations

from .. import config
from ..quiz_manager import QuizManager
from ..storage import QuestionStore, ResultsLog
from .generate import generate_questions_flow
from .manage import manage_questions_flow
from .quiz import practice_mode, test_mode
from .stats import view_statistics
from .terminal import ask, console, info, warning

MENU = """
[bold]==== AI-Powered Learning Companion ====[/bold]
1) Generate Questions (LLM)
2) View Statistics
3) Practice Mode
4) Test Mode
5) Manage Questions (Enable/Disable/List)
6) Quit"""

ACTIONS = {
    "1": generate_questions_flow,
    "2": view_statistics,
    "3": practice_mode,
    "4": test_mode,
    "5": manage_questions_flow,
}


def build_manager() -> QuizManager:
    store = QuestionStore(config.QUESTIONS_FILE)
    results_log = ResultsLog(config.RESULTS_FILE)
    return QuizManager(store=store, results_log=results_log)


def main() -> None:
    manager = build_manager()
    while True:
        console.print(MENU)
        choice = ask("\nChoose an option: ")
        if choice == "6":
            info("Goodbye!")
            return
        action = ACTIONS.get(choice)
        if action is None:
            warning("Invalid choice, try again.")
        else:
            action(manager)
