"""Prompt templates for the Learning Companion's LLM calls.

Kept separate from llm_client.py so prompt wording can be read, reviewed,
and iterated on without touching any networking/parsing/error-handling
code. Each prompt is versioned (PROMPT_VERSION) so that a change in
wording can be correlated with a change in generated/evaluated output
if question quality or grading behavior ever shifts unexpectedly.

Each public function returns a (system, user) tuple ready to pass
straight into LLMClient._chat(system, user).
"""

from __future__ import annotations

PROMPT_VERSION = "1.0"


# ---------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------

GENERATE_QUESTIONS_SYSTEM = (
    "You are an expert quiz writer helping a student study. "
    "You always reply with STRICT JSON only, no commentary, no markdown fences."
)

GENERATE_QUESTIONS_USER_TEMPLATE = """Generate study questions about the topic: "{topic}".

Produce exactly {num_mcq} multiple-choice questions and {num_freeform} freeform (open-ended)
questions.

Respond with ONLY a JSON array. Each element must be an object with these keys:
- "q_type": either "mcq" or "freeform"
- "text": the question text
- "options": for mcq, a list of 4 distinct answer strings (omit or use [] for freeform)
- "correct_answer": for mcq, the exact text of the correct option (must match one entry in
  "options"); for freeform, a concise reference/model answer.

Example format:
[
  {{"q_type": "mcq", "text": "...", "options": ["A", "B", "C", "D"], "correct_answer": "B"}},
  {{"q_type": "freeform", "text": "...", "options": [], "correct_answer": "..."}}
]

Return only the JSON array, nothing else."""


def generate_questions_prompt(topic: str, num_mcq: int, num_freeform: int) -> tuple[str, str]:
    """Build the (system, user) prompt pair for question generation."""
    user = GENERATE_QUESTIONS_USER_TEMPLATE.format(
        topic=topic, num_mcq=num_mcq, num_freeform=num_freeform
    )
    return GENERATE_QUESTIONS_SYSTEM, user


# ---------------------------------------------------------------------
# Freeform answer evaluation
# ---------------------------------------------------------------------

EVALUATE_FREEFORM_SYSTEM = (
    "You are a strict but fair teaching assistant grading a student's short answer. "
    "You always reply with STRICT JSON only, no commentary, no markdown fences."
)

EVALUATE_FREEFORM_USER_TEMPLATE = """Question: {question_text}
Reference (model) answer: {reference_answer}
Student's answer: {user_answer}

Judge whether the student's answer is substantively correct compared to the reference answer.
Minor wording differences are fine as long as the core meaning is right.

Respond with ONLY a JSON object of the form:
{{"verdict": "correct" or "incorrect", "explanation": "one brief sentence"}}"""


def evaluate_freeform_prompt(
    question_text: str, reference_answer: str, user_answer: str
) -> tuple[str, str]:
    """Build the (system, user) prompt pair for freeform answer evaluation."""
    user = EVALUATE_FREEFORM_USER_TEMPLATE.format(
        question_text=question_text,
        reference_answer=reference_answer,
        user_answer=user_answer,
    )
    return EVALUATE_FREEFORM_SYSTEM, user
