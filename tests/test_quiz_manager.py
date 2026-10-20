import os
import random
import tempfile
import unittest
from collections import Counter
from unittest.mock import MagicMock

from learning_companion.llm_client import LLMError
from learning_companion.models import Question, MCQ, FREEFORM
from learning_companion.quiz_manager import QuizManager, compute_weight, weighted_choice
from learning_companion.storage import QuestionStore, ResultsLog


class TestQuizManagerLogic(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        q_path = os.path.join(self.tmpdir, "questions.json")
        r_path = os.path.join(self.tmpdir, "results.txt")
        self.manager = QuizManager(
            store=QuestionStore(q_path),
            results_log=ResultsLog(r_path),
        )

    def test_mcq_evaluation_case_and_whitespace_insensitive(self):
        q = Question(topic="t", text="2+2?", q_type=MCQ, correct_answer="4", options=["3", "4"])
        self.assertTrue(self.manager.evaluate_mcq(q, "4"))
        self.assertTrue(self.manager.evaluate_mcq(q, " 4 "))
        self.assertFalse(self.manager.evaluate_mcq(q, "3"))

    def test_compute_weight_prioritizes_incorrect_and_unseen_questions(self):
        never_shown = Question(topic="t", text="q1", q_type=FREEFORM, correct_answer="a")
        mostly_correct = Question(topic="t", text="q2", q_type=FREEFORM, correct_answer="a")
        mostly_correct.times_shown = 10
        mostly_correct.times_correct = 9
        mostly_wrong = Question(topic="t", text="q3", q_type=FREEFORM, correct_answer="a")
        mostly_wrong.times_shown = 10
        mostly_wrong.times_correct = 1

        self.assertGreater(compute_weight(mostly_wrong), compute_weight(mostly_correct))
        self.assertGreater(compute_weight(never_shown), compute_weight(mostly_correct))

    def test_weighted_choice_favors_incorrect_over_many_draws(self):
        # Seeded so this test is deterministic and can never flake, while
        # still exercising the real random.choices code path (not mocked).
        random.seed(1234)
        easy = Question(topic="t", text="easy", q_type=FREEFORM, correct_answer="a")
        easy.times_shown = 20
        easy.times_correct = 20
        hard = Question(topic="t", text="hard", q_type=FREEFORM, correct_answer="a")
        hard.times_shown = 20
        hard.times_correct = 0

        picks = [weighted_choice([easy, hard]).text for _ in range(2000)]
        counts = Counter(picks)
        self.assertGreater(counts["hard"], counts["easy"])

    def test_pick_test_questions_no_duplicates_and_respects_active_flag(self):
        for i in range(5):
            q = Question(topic="t", text=f"q{i}", q_type=FREEFORM, correct_answer="a")
            if i == 0:
                q.active = False
            self.manager.questions.append(q)

        picks = self.manager.pick_test_questions(10)  # ask for more than available active
        ids = [q.id for q in picks]
        self.assertEqual(len(ids), len(set(ids)))  # no duplicates
        self.assertEqual(len(picks), 4)  # only 4 of the 5 are active
        self.assertTrue(all(q.active for q in picks))

    def test_failed_llm_evaluation_does_not_corrupt_stats(self):
        """A network/API failure during freeform evaluation is not evidence
        the student was wrong, so it must propagate as LLMError rather than
        being swallowed into a recorded incorrect attempt."""
        q = Question(topic="t", text="q", q_type=FREEFORM, correct_answer="a")
        self.manager.questions.append(q)

        fake_llm = MagicMock()
        fake_llm.evaluate_freeform.side_effect = LLMError("simulated network failure")
        self.manager._llm_client = fake_llm

        with self.assertRaises(LLMError):
            self.manager.evaluate_freeform(q, "my answer")

        # The failure must not have touched the question's stats.
        self.assertEqual(q.times_shown, 0)
        self.assertEqual(q.times_correct, 0)

    def test_successful_llm_evaluation_passes_through_unchanged(self):
        q = Question(topic="t", text="q", q_type=FREEFORM, correct_answer="a")
        fake_llm = MagicMock()
        fake_llm.evaluate_freeform.return_value = (True, "Well explained.")
        self.manager._llm_client = fake_llm

        correct, explanation = self.manager.evaluate_freeform(q, "my answer")
        self.assertTrue(correct)
        self.assertEqual(explanation, "Well explained.")

    def test_set_active_persists_across_reload_and_handles_unknown_id(self):
        q = Question(topic="t", text="q", q_type=FREEFORM, correct_answer="a", active=True)
        self.manager.add_question(q)

        self.assertTrue(self.manager.set_active(q.id, False))
        self.assertFalse(self.manager.find_by_id(q.id).active)

        reloaded = QuizManager(store=self.manager.store, results_log=self.manager.results_log)
        self.assertFalse(reloaded.find_by_id(q.id).active)

        self.assertFalse(self.manager.set_active("does-not-exist", True))


if __name__ == "__main__":
    unittest.main()
