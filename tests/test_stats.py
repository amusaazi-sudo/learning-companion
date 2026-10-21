"""The statistics table shows the right labels and never breaks on bracketed text."""

import io
import unittest

from rich.console import Console

from learning_companion.cli.stats import build_table, score_label
from learning_companion.models import FREEFORM, Question


def question(times_shown=0, times_correct=0, text="Q"):
    q = Question(topic="t", text=text, q_type=FREEFORM, correct_answer="a")
    q.times_shown, q.times_correct = times_shown, times_correct
    return q


class TestScoreLabel(unittest.TestCase):
    def test_never_shown_is_a_dash(self):
        self.assertEqual(score_label(question()), "[dim]-[/dim]")

    def test_colors_follow_the_score(self):
        self.assertIn("green", score_label(question(10, 9)))
        self.assertIn("yellow", score_label(question(10, 5)))
        self.assertIn("red", score_label(question(10, 1)))


class TestBuildTable(unittest.TestCase):
    def render(self, questions):
        console = Console(record=True, width=200, file=io.StringIO())
        console.print(build_table(questions))
        return console.export_text()

    def test_square_brackets_in_text_are_printed_literally(self):
        output = self.render([question(text="What does [bold] do?")])
        self.assertIn("What does [bold] do?", output)


if __name__ == "__main__":
    unittest.main()
