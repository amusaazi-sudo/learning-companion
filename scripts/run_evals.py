"""Run the prompt evaluation set against the real LLM.

Run after changing a prompt (and bumping PROMPT_VERSION) to check that grading
and question generation still behave. Uses your API key and costs a few cents.

    python -m scripts.run_evals
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.markup import escape
from rich.table import Table

from learning_companion.llm_client import LLMClient, LLMError
from learning_companion.prompts import PROMPT_VERSION

CASES = json.loads((Path(__file__).parent.parent / "evals" / "cases.json").read_text(encoding="utf-8"))
console = Console()


def run_grading(client: LLMClient, table: Table) -> int:
    passed = 0
    for case in CASES["grading"]:
        try:
            is_correct, _ = client.evaluate_freeform(case["question"], case["reference"], case["answer"])
            got = "correct" if is_correct else "incorrect"
        except LLMError as exc:
            got = f"error: {exc}"
        ok = got == case["expected"]
        passed += ok
        table.add_row("grading", case["name"], case["expected"], escape(got), "[green]PASS[/]" if ok else "[red]FAIL[/]")
    return passed


def run_generation(client: LLMClient, table: Table) -> int:
    passed = 0
    for case in CASES["generation"]:
        expected = f"{case['num_mcq']} mcq + {case['num_freeform']} freeform"
        try:
            questions = client.generate_questions(case["topic"], case["num_mcq"], case["num_freeform"])
            mcqs = [q for q in questions if q["q_type"] == "mcq"]
            got = f"{len(mcqs)} mcq + {len(questions) - len(mcqs)} freeform"
            ok = got == expected and all(len(q["options"]) == 4 for q in mcqs)
        except LLMError as exc:
            got, ok = f"error: {exc}", False
        passed += ok
        table.add_row("generation", case["topic"], expected, escape(got), "[green]PASS[/]" if ok else "[red]FAIL[/]")
    return passed


def main() -> None:
    client = LLMClient()
    table = Table(title=f"Prompt evaluation (prompt version {PROMPT_VERSION}, model {client.model})")
    for column in ("Kind", "Case", "Expected", "Got", "Result"):
        table.add_column(column)

    passed = run_grading(client, table) + run_generation(client, table)
    total = len(CASES["grading"]) + len(CASES["generation"])
    console.print(table)
    console.print(f"[bold]{passed}/{total} cases passed[/bold]")


if __name__ == "__main__":
    main()
