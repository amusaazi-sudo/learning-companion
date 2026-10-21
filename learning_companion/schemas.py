"""Shapes of the answers we expect back from the LLM.

These Pydantic models are passed to OpenAI's Structured Outputs feature, so
the model is forced to reply in exactly this shape and the SDK hands us
ready-made Python objects instead of raw JSON text.
"""

from typing import List, Literal

from pydantic import BaseModel


class GeneratedQuestion(BaseModel):
    q_type: Literal["mcq", "freeform"]
    text: str
    options: List[str]  # 4 choices for mcq, empty for freeform
    correct_answer: str


class QuestionGenerationResponse(BaseModel):
    questions: List[GeneratedQuestion]


class EvaluationResponse(BaseModel):
    verdict: Literal["correct", "incorrect"]
    explanation: str
