"""All calls to the OpenAI API live here.

Uses Structured Outputs: each request names a Pydantic schema (see
schemas.py) and the SDK returns a parsed object, so there is no hand-written
JSON parsing. Every failure is turned into a single LLMError, so the rest of
the app never needs to know about openai-specific exceptions.
"""

from __future__ import annotations

import os
from typing import List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel

from . import config
from .prompts import evaluate_freeform_prompt, generate_questions_prompt
from .schemas import EvaluationResponse, GeneratedQuestion, QuestionGenerationResponse

try:
    from openai import APIConnectionError, APIError, AuthenticationError, OpenAI, RateLimitError
except ImportError:  # pragma: no cover - only when openai isn't installed
    OpenAI = None
    APIError = APIConnectionError = RateLimitError = AuthenticationError = Exception

Schema = TypeVar("Schema", bound=BaseModel)


class LLMError(Exception):
    """Raised whenever the LLM call fails or returns something unusable."""


class LLMClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise LLMError("No OpenAI API key found. Set OPENAI_API_KEY in your .env file.")
        if OpenAI is None:
            raise LLMError("The 'openai' package is not installed. Run: pip install -e .")
        self.model = model or config.OPENAI_MODEL
        self._client = OpenAI(api_key=api_key)

    def _ask(self, system: str, user: str, schema: Type[Schema], temperature: float) -> Schema:
        """Send one request and return the reply parsed into `schema`."""
        try:
            completion = self._client.chat.completions.parse(
                model=self.model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format=schema,
            )
        except AuthenticationError as exc:
            raise LLMError(f"Authentication failed - check your API key: {exc}") from exc
        except RateLimitError as exc:
            raise LLMError(f"Rate limit hit, please try again shortly: {exc}") from exc
        except APIConnectionError as exc:
            raise LLMError(f"Could not reach the OpenAI API (network issue): {exc}") from exc
        except APIError as exc:
            raise LLMError(f"OpenAI API returned an error: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - never crash the app on an unexpected error
            raise LLMError(f"Unexpected error calling the OpenAI API: {exc}") from exc

        message = completion.choices[0].message
        if message.refusal:
            raise LLMError(f"The model declined to answer: {message.refusal}")
        if message.parsed is None:
            raise LLMError("The model returned an empty answer.")
        return message.parsed

    def generate_questions(self, topic: str, num_mcq: int = 3, num_freeform: int = 2) -> List[dict]:
        """Return usable questions as plain dicts (q_type, text, options, correct_answer)."""
        system, user = generate_questions_prompt(topic, num_mcq, num_freeform)
        response = self._ask(system, user, QuestionGenerationResponse, temperature=0.7)
        questions = [to_dict(q) for q in response.questions if is_usable(q)]
        if not questions:
            raise LLMError("The model did not return any usable questions.")
        return questions

    def evaluate_freeform(self, question_text: str, reference_answer: str, user_answer: str) -> Tuple[bool, str]:
        """Return (is_correct, explanation) for a student's freeform answer."""
        system, user = evaluate_freeform_prompt(question_text, reference_answer, user_answer)
        result = self._ask(system, user, EvaluationResponse, temperature=0.0)
        return result.verdict == "correct", result.explanation.strip()


def is_usable(q: GeneratedQuestion) -> bool:
    """The schema guarantees the shape; this checks the content makes sense."""
    if not q.text.strip() or not q.correct_answer.strip():
        return False
    if q.q_type == "mcq":
        options = [o.strip().lower() for o in q.options]
        return len(options) >= 2 and q.correct_answer.strip().lower() in options
    return True


def to_dict(q: GeneratedQuestion) -> dict:
    return {
        "q_type": q.q_type,
        "text": q.text.strip(),
        "options": [o.strip() for o in q.options] if q.q_type == "mcq" else [],
        "correct_answer": q.correct_answer.strip(),
    }
