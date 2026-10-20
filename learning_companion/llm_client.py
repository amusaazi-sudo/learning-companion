"""Wrapper around the OpenAI Chat Completions API used by the Learning Companion.

Kept isolated from the rest of the app so that:
  * the API key handling / error handling lives in one place, and
  * the rest of the code (and the unit tests) never need to import `openai`
    directly or talk to the network.
"""

from __future__ import annotations

import json
import os
from typing import List, Optional, Tuple

from .prompts import generate_questions_prompt, evaluate_freeform_prompt

try:
    from openai import (
        OpenAI,
        APIError,
        APIConnectionError,
        RateLimitError,
        AuthenticationError,
    )
except ImportError:  # pragma: no cover - exercised only when openai isn't installed
    OpenAI = None
    APIError = APIConnectionError = RateLimitError = AuthenticationError = Exception


class LLMError(Exception):
    """Raised whenever the LLM API call fails or returns something unusable."""


class LLMClient:
    """Thin wrapper responsible for all LLM calls (question generation + evaluation)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise LLMError(
                "No OpenAI API key found. Set the OPENAI_API_KEY environment variable "
                "(see .env.example) before using LLM-powered features."
            )
        if OpenAI is None:
            raise LLMError(
                "The 'openai' package is not installed. Run `pip install -r requirements.txt`."
            )
        self.model = model
        self._client = OpenAI(api_key=api_key)

    # ------------------------------------------------------------------
    def _chat(self, system: str, user: str, temperature: float = 0.7) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except AuthenticationError as exc:
            raise LLMError(f"Authentication failed - check your API key: {exc}") from exc
        except RateLimitError as exc:
            raise LLMError(f"Rate limit hit, please try again shortly: {exc}") from exc
        except APIConnectionError as exc:
            raise LLMError(f"Could not connect to the LLM API (network issue): {exc}") from exc
        except APIError as exc:
            raise LLMError(f"LLM API returned an error: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - surface anything unexpected, don't crash the app
            raise LLMError(f"Unexpected error calling the LLM API: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise LLMError("LLM returned an empty response.")
        return content.strip()

    @staticmethod
    def _extract_json(raw: str):
        """Best-effort extraction of a JSON object/array out of an LLM response.

        Handles the common cases of the model wrapping JSON in ```json fences
        or adding stray text around the JSON payload.
        """
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            starts = [i for i in (raw.find("["), raw.find("{")) if i != -1]
            start = min(starts) if starts else -1
            end = max(raw.rfind("]"), raw.rfind("}"))
            if start != -1 and end != -1:
                try:
                    return json.loads(raw[start : end + 1])
                except json.JSONDecodeError:
                    pass
            raise LLMError(f"Could not parse JSON from LLM response: {exc}\nRaw: {raw[:300]}") from exc

    # ------------------------------------------------------------------
    def generate_questions(self, topic: str, num_mcq: int = 3, num_freeform: int = 2) -> List[dict]:
        """Ask the LLM for a mix of MCQ + freeform questions on `topic`.

        Returns a list of plain dicts with keys: q_type, text, options, correct_answer.
        """
        system, user = generate_questions_prompt(topic, num_mcq, num_freeform)

        raw = self._chat(system, user, temperature=0.7)
        parsed = self._extract_json(raw)
        if not isinstance(parsed, list):
            raise LLMError("Expected a JSON array of questions from the LLM.")

        questions: List[dict] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            q_type = str(item.get("q_type", "")).lower().strip()
            text = str(item.get("text", "")).strip()
            correct_answer = str(item.get("correct_answer", "")).strip()
            options = item.get("options") or []
            if q_type not in ("mcq", "freeform") or not text or not correct_answer:
                continue
            if q_type == "mcq" and (not isinstance(options, list) or len(options) < 2):
                continue
            questions.append(
                {
                    "q_type": q_type,
                    "text": text,
                    "options": [str(o).strip() for o in options] if q_type == "mcq" else [],
                    "correct_answer": correct_answer,
                }
            )

        if not questions:
            raise LLMError("LLM did not return any usable questions.")
        return questions

    # ------------------------------------------------------------------
    def evaluate_freeform(
        self, question_text: str, reference_answer: str, user_answer: str
    ) -> Tuple[bool, str]:
        """Ask the LLM to judge a freeform answer.

        Returns (is_correct, explanation).
        """
        system, user = evaluate_freeform_prompt(question_text, reference_answer, user_answer)

        raw = self._chat(system, user, temperature=0.0)
        parsed = self._extract_json(raw)
        if not isinstance(parsed, dict) or "verdict" not in parsed:
            raise LLMError("LLM evaluation response was missing a verdict.")
        verdict = str(parsed.get("verdict", "")).lower().strip()
        explanation = str(parsed.get("explanation", "")).strip()
        return verdict.startswith("correct"), explanation
