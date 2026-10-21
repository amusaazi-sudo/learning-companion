"""Tests for LLMClient. The OpenAI SDK is always mocked, so no network or API key is used."""

import unittest
from unittest.mock import MagicMock, patch

from openai import APIConnectionError, AuthenticationError, RateLimitError

from learning_companion.llm_client import LLMClient, LLMError
from learning_companion.schemas import EvaluationResponse, GeneratedQuestion, QuestionGenerationResponse


def make_client() -> LLMClient:
    with patch("learning_companion.llm_client.OpenAI"):
        return LLMClient(api_key="test-key-not-real", model="test-model")


def reply(parsed=None, refusal=None):
    """Build a fake SDK response holding one message."""
    message = MagicMock(parsed=parsed, refusal=refusal)
    return MagicMock(choices=[MagicMock(message=message)])


def sdk_error(cls):
    """Create an OpenAI exception without its real constructor, which needs HTTP
    objects whose library changes between SDK versions. Our code only checks the
    exception's type and message, so that is all we set."""
    error = cls.__new__(cls)
    Exception.__init__(error, "simulated")
    return error


def mcq(text="Q", options=("a", "b", "c", "d"), answer="a"):
    return GeneratedQuestion(q_type="mcq", text=text, options=list(options), correct_answer=answer)


def freeform(text="Q", answer="A model answer"):
    return GeneratedQuestion(q_type="freeform", text=text, options=[], correct_answer=answer)


class TestErrorHandling(unittest.TestCase):
    """Every failure must become one LLMError with a helpful message."""

    def assert_llm_error(self, side_effect, expected_words):
        client = make_client()
        client._client.chat.completions.parse = MagicMock(side_effect=side_effect)
        with self.assertRaises(LLMError) as ctx:
            client.evaluate_freeform("Q", "ref", "answer")
        self.assertIn(expected_words, str(ctx.exception))

    def test_authentication_failure(self):
        self.assert_llm_error(sdk_error(AuthenticationError), "Authentication failed")

    def test_rate_limit(self):
        self.assert_llm_error(sdk_error(RateLimitError), "Rate limit")

    def test_network_failure(self):
        self.assert_llm_error(sdk_error(APIConnectionError), "network issue")

    def test_unexpected_exception(self):
        self.assert_llm_error(RuntimeError("boom"), "Unexpected error")

    def test_model_refusal(self):
        client = make_client()
        client._client.chat.completions.parse = MagicMock(return_value=reply(refusal="I can't help with that."))
        with self.assertRaises(LLMError) as ctx:
            client.evaluate_freeform("Q", "ref", "answer")
        self.assertIn("declined", str(ctx.exception))

    def test_empty_parsed_answer(self):
        client = make_client()
        client._client.chat.completions.parse = MagicMock(return_value=reply(parsed=None))
        with self.assertRaises(LLMError):
            client.evaluate_freeform("Q", "ref", "answer")


class TestGenerateQuestions(unittest.TestCase):
    def generate(self, *questions):
        client = make_client()
        parse = MagicMock(return_value=reply(parsed=QuestionGenerationResponse(questions=list(questions))))
        client._client.chat.completions.parse = parse
        return client.generate_questions("topic", 1, 1), parse

    def test_sends_the_question_schema(self):
        _, parse = self.generate(mcq())
        self.assertIs(parse.call_args.kwargs["response_format"], QuestionGenerationResponse)

    def test_returns_plain_dicts(self):
        result, _ = self.generate(mcq(), freeform())
        self.assertEqual([q["q_type"] for q in result], ["mcq", "freeform"])
        self.assertEqual(result[1]["options"], [])

    def test_drops_mcq_whose_answer_is_not_an_option(self):
        result, _ = self.generate(mcq(text="good"), mcq(text="bad", answer="z"))
        self.assertEqual([q["text"] for q in result], ["good"])

    def test_drops_mcq_with_fewer_than_two_options(self):
        result, _ = self.generate(mcq(text="good"), mcq(text="bad", options=["a"]))
        self.assertEqual([q["text"] for q in result], ["good"])

    def test_drops_blank_questions(self):
        result, _ = self.generate(freeform(text="good"), freeform(text="   "))
        self.assertEqual(len(result), 1)

    def test_raises_when_nothing_is_usable(self):
        with self.assertRaises(LLMError):
            self.generate(mcq(answer="not-an-option"))


class TestEvaluateFreeform(unittest.TestCase):
    def evaluate(self, verdict, explanation="Because."):
        client = make_client()
        parse = MagicMock(return_value=reply(parsed=EvaluationResponse(verdict=verdict, explanation=explanation)))
        client._client.chat.completions.parse = parse
        return client.evaluate_freeform("Q", "ref", "answer"), parse

    def test_correct_verdict(self):
        (is_correct, explanation), _ = self.evaluate("correct", " Nice work. ")
        self.assertTrue(is_correct)
        self.assertEqual(explanation, "Nice work.")

    def test_incorrect_verdict(self):
        (is_correct, _), _ = self.evaluate("incorrect")
        self.assertFalse(is_correct)

    def test_grading_is_deterministic_and_uses_the_evaluation_schema(self):
        _, parse = self.evaluate("correct")
        self.assertEqual(parse.call_args.kwargs["temperature"], 0.0)
        self.assertIs(parse.call_args.kwargs["response_format"], EvaluationResponse)


if __name__ == "__main__":
    unittest.main()