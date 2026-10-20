import unittest

from learning_companion.prompts import (
    generate_questions_prompt,
    evaluate_freeform_prompt,
)


class TestGenerateQuestionsPrompt(unittest.TestCase):
    def test_substitutes_topic_and_counts(self):
        system, user = generate_questions_prompt("Python Dictionaries", 3, 2)
        self.assertIn("Python Dictionaries", user)
        self.assertIn("exactly 3 multiple-choice", user)
        self.assertIn("2 freeform", user)
        self.assertIn("STRICT JSON only", system)

    def test_example_json_braces_survive_formatting(self):
        # Regression guard: the literal {{ }} example JSON in the template
        # must render as real single braces after .format(), not stay doubled.
        _, user = generate_questions_prompt("Any Topic", 1, 1)
        self.assertIn('{"q_type": "mcq"', user)
        self.assertNotIn("{{", user)


class TestEvaluateFreeformPrompt(unittest.TestCase):
    def test_substitutes_all_three_fields(self):
        system, user = evaluate_freeform_prompt("What is X?", "X is Y.", "I think X is Y")
        self.assertIn("What is X?", user)
        self.assertIn("X is Y.", user)
        self.assertIn("I think X is Y", user)
        self.assertIn("grading a student's short answer", system)


if __name__ == "__main__":
    unittest.main()
