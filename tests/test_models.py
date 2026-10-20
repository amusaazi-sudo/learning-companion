import unittest

from learning_companion.models import Question, MCQ, FREEFORM


class TestQuestion(unittest.TestCase):
    def test_correct_percentage_no_attempts(self):
        q = Question(topic="t", text="q", q_type=FREEFORM, correct_answer="a")
        self.assertEqual(q.correct_percentage, 0.0)

    def test_correct_percentage_computation(self):
        q = Question(topic="t", text="q", q_type=MCQ, correct_answer="a", options=["a", "b"])
        q.record_attempt(True)
        q.record_attempt(False)
        q.record_attempt(True)
        self.assertEqual(q.times_shown, 3)
        self.assertEqual(q.times_correct, 2)
        self.assertEqual(q.correct_percentage, 66.7)

    def test_unique_ids_generated(self):
        q1 = Question(topic="t", text="q1", q_type=FREEFORM, correct_answer="a")
        q2 = Question(topic="t", text="q2", q_type=FREEFORM, correct_answer="a")
        self.assertNotEqual(q1.id, q2.id)

    def test_serialization_roundtrip(self):
        q = Question(
            topic="Python",
            text="What is a list?",
            q_type=MCQ,
            correct_answer="A mutable sequence",
            options=["A mutable sequence", "A number"],
        )
        data = q.to_dict()
        rebuilt = Question.from_dict(data)
        self.assertEqual(q.id, rebuilt.id)
        self.assertEqual(q.text, rebuilt.text)
        self.assertEqual(q.options, rebuilt.options)


if __name__ == "__main__":
    unittest.main()
