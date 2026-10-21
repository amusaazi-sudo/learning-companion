"""Shared terminal helpers: one Rich console and small input/output functions.

Text that comes from users or the LLM is always passed through `escape()`
before printing, because Rich treats anything in [square brackets] as styling.
"""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.markup import escape

console = Console()


def info(text: str) -> None:
    console.print(escape(text))


def success(text: str) -> None:
    console.print(f"[green]{escape(text)}[/green]")


def warning(text: str) -> None:
    console.print(f"[yellow]{escape(text)}[/yellow]")


def error(text: str) -> None:
    console.print(f"[red]{escape(text)}[/red]")


def divider() -> None:
    console.rule(style="dim")


def ask(prompt: str) -> str:
    """Plain input() so prompts like '[3]' are never mistaken for Rich styling."""
    return input(prompt).strip()


def ask_int(prompt: str, default: Optional[int] = None) -> int:
    while True:
        raw = ask(prompt)
        if not raw and default is not None:
            return default
        try:
            return int(raw)
        except ValueError:
            warning("Please enter a whole number.")
