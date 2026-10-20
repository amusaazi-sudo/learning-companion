"""Tests for LLMClient that never touch the real network.

All OpenAI-facing behavior is exercised through unittest.mock, either by
patching LLMClient._chat directly (to test parsing/validation) or by
patching the underlying OpenAI SDK client (to test error translation).
"""

import unittest
from unittest.mock import MagicMock, patch

from learning_companion.llm_client import LLMClient, LLMError


def make_client() -> LLMClient:
    """Build an LLMClient without needing a real API key or network call."""
    with patch("learning_companion.llm_client.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        return LLMClient(api_key="test-key-not-real")


class TestExtractJson(unittest.TestCase):
    def setUp(self):
        self.client = make_client()

    def test_parses_clean_json_array(self):
        raw = '[{"q_type": "mcq", "text": "q", "options": ["a", "b"], "correct_answer": "a"}]'
        result = self.client._extract_json(raw)
        self.assertEqual(result[0]["text"], "q")

    def test_strips_markdown_code_fence(self):
        raw = '```json\n[{"q_type": "freeform", "text": "q", "options": [], "correct_answer": "a"}]\n```'
        result = self.client._extract_json(raw)
        self.assertEqual(result[0]["q_type"], "freeform")

    def test_extracts_json_from_surrounding_commentary(self):
        raw = 'Sure, here you go:\n[{"q_type": "mcq", "text": "q", "options": ["a", "b"], "correct_answer": "a"}]\nHope that helps!'
        result = self.client._extract_json(raw)
        self.assertEqual(result[0]["q_type"], "mcq")

    def test_raises_llm_error_on_unparseable_garbage(self):
        with self.assertRaises(LLMError):
            self.client._extract_json("this is not json at all {{{")


class TestGenerateQuestionsValidation(unittest.TestCase):
    def setUp(self):
        self.client = make_client()

    def test_drops_items_missing_required_fields(self):
        good = {"q_type": "mcq", "text": "Q1", "options": ["a", "b"], "correct_answer": "a"}
        missing_answer = {"q_type": "mcq", "text": "Q2", "options": ["a", "b"], "correct_answer": ""}
        with patch.object(self.client, "_chat", return_value="ignored"), \
             patch.object(self.client, "_extract_json", return_value=[good, missing_answer]):
            result = self.client.generate_questions("topic", 1, 0)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["text"], "Q1")

    def test_drops_mcq_with_fewer_than_two_options(self):
        bad_mcq = {"q_type": "mcq", "text": "Q", "options": ["only-one"], "correct_answer": "only-one"}
        with patch.object(self.client, "_chat", return_value="ignored"), \
             patch.object(self.client, "_extract_json", return_value=[bad_mcq]):
            with self.assertRaises(LLMError):
                self.client.generate_questions("topic", 1, 0)

    def test_raises_if_response_is_not_a_list(self):
        with patch.object(self.client, "_chat", return_value="ignored"), \
             patch.object(self.client, "_extract_json", return_value={"not": "a list"}):
            with self.assertRaises(LLMError):
                self.client.generate_questions("topic", 1, 0)


class TestEvaluateFreeform(unittest.TestCase):
    def setUp(self):
        self.client = make_client()

    def test_returns_true_on_correct_verdict(self):
        with patch.object(self.client, "_chat", return_value="ignored"), \
             patch.object(self.client, "_extract_json",
                          return_value={"verdict": "correct", "explanation": "Nice work."}):
            is_correct, explanation = self.client.evaluate_freeform("Q", "ref", "answer")
        self.assertTrue(is_correct)
        self.assertEqual(explanation, "Nice work.")

    def test_returns_false_on_incorrect_verdict(self):
        with patch.object(self.client, "_chat", return_value="ignored"), \
             patch.object(self.client, "_extract_json",
                          return_value={"verdict": "incorrect", "explanation": "Missed the key point."}):
            is_correct, _ = self.client.evaluate_freeform("Q", "ref", "answer")
        self.assertFalse(is_correct)

    def test_raises_if_verdict_key_missing(self):
        with patch.object(self.client, "_chat", return_value="ignored"), \
             patch.object(self.client, "_extract_json", return_value={"explanation": "no verdict here"}):
            with self.assertRaises(LLMError):
                self.client.evaluate_freeform("Q", "ref", "answer")


class TestChatErrorTranslation(unittest.TestCase):
    """Confirms real SDK exceptions get translated into a single LLMError type."""

    def test_generic_exception_becomes_llm_error(self):
        client = make_client()
        client._client.chat.completions.create = MagicMock(side_effect=RuntimeError("boom"))
        with self.assertRaises(LLMError):
            client._chat("system", "user")

    def test_empty_response_content_raises_llm_error(self):
        client = make_client()
        fake_response = MagicMock()
        fake_response.choices = [MagicMock(message=MagicMock(content=""))]
        client._client.chat.completions.create = MagicMock(return_value=fake_response)
        with self.assertRaises(LLMError):
            client._chat("system", "user")


if __name__ == "__main__":
    unittest.main()
