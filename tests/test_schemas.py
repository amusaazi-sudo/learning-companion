"""The schemas reject replies that don't match the expected shape."""

import unittest

from pydantic import ValidationError

from learning_companion.schemas import EvaluationResponse, GeneratedQuestion


class TestSchemas(unittest.TestCase):
    def test_question_type_must_be_mcq_or_freeform(self):
        with self.assertRaises(ValidationError):
            GeneratedQuestion(q_type="essay", text="Q", options=[], correct_answer="A")

    def test_verdict_must_be_correct_or_incorrect(self):
        with self.assertRaises(ValidationError):
            EvaluationResponse(verdict="maybe", explanation="Not sure.")

    def test_missing_field_is_rejected(self):
        with self.assertRaises(ValidationError):
            EvaluationResponse(verdict="correct")


if __name__ == "__main__":
    unittest.main()
