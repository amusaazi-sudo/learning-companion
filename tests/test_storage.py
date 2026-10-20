import os
import tempfile
import unittest

from learning_companion.models import Question, MCQ
from learning_companion.storage import QuestionStore, ResultsLog


class TestQuestionStore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "sub", "questions.json")

    def test_load_returns_empty_list_when_file_missing(self):
        store = QuestionStore(self.path)
        self.assertEqual(store.load(), [])

    def test_save_then_load_roundtrip(self):
        store = QuestionStore(self.path)
        q = Question(topic="Math", text="1+1?", q_type=MCQ, correct_answer="2", options=["1", "2"])
        store.save([q])

        loaded = store.load()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].id, q.id)
        self.assertEqual(loaded[0].text, "1+1?")
        self.assertEqual(loaded[0].options, ["1", "2"])


class TestResultsLog(unittest.TestCase):
    def test_append_result_writes_line(self):
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, "results.txt")
        log = ResultsLog(path)
        log.append_result(7, 10)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Score: 7/10", content)


if __name__ == "__main__":
    unittest.main()
