"""Menu option 2: the question statistics table."""

from __future__ import annotations

from rich.markup import escape
from rich.table import Table

from ..models import Question
from ..quiz_manager import QuizManager
from .terminal import console, warning


def score_label(q: Question) -> str:
    """Green = doing well, yellow = so-so, red = needs practice, dim dash = never shown."""
    if q.times_shown == 0:
        return "[dim]-[/dim]"
    pct = q.correct_percentage
    color = "green" if pct >= 70 else "yellow" if pct >= 40 else "red"
    return f"[{color}]{pct}%[/{color}]"


def build_table(questions: list[Question]) -> Table:
    table = Table(title="Question Statistics")
    table.add_column("ID", style="dim")
    table.add_column("Active", justify="center")
    table.add_column("Type")
    table.add_column("Source")
    table.add_column("Shown", justify="right")
    table.add_column("Correct %", justify="right")
    table.add_column("Topic")
    table.add_column("Question")

    for q in questions:
        table.add_row(
            q.id,
            "[green]Yes[/green]" if q.active else "[red]No[/red]",
            q.q_type,
            q.source,
            str(q.times_shown),
            score_label(q),
            escape(q.topic),
            escape(q.text),
        )
    return table


def view_statistics(manager: QuizManager) -> None:
    if not manager.questions:
        warning("No questions saved yet.")
        return
    console.print(build_table(manager.questions))
