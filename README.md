# AI-Powered Learning Companion

A command-line study tool that uses an LLM (OpenAI's API) to generate quiz
questions on any topic, grade freeform answers, and track your progress over
time with weighted practice and randomized tests.

## Features

- **Generate Questions (LLM)**: enter a topic and get a mix of multiple-choice
  and freeform questions. Review, edit or reject each one before it's saved.
- **View Statistics**: a colour-coded table of every saved question: ID,
  active status, type, source, times shown, correct percentage and topic.
- **Practice Mode**: endless practice with *weighted* selection. Questions
  you miss more often come up more often; ones you've mastered fade back.
- **Test Mode**: choose how many questions, answer each once with no
  repeats, and your score is appended to `data/results.txt`.
- **Manage Questions**: list all questions, or enable/disable one by ID
  after a confirmation step. Disabled questions never appear in Practice or
  Test mode.

## Setup

1. **Create a virtual environment and install the project:**

   ```bash
   python -m venv venv
   source venv/Scripts/activate      # Windows Git Bash. Mac/Linux: source venv/bin/activate
   pip install -e ".[dev]"
   ```

   `-e` installs the project in editable mode, and `[dev]` adds the test tools.

2. **Add your OpenAI API key.** Copy `.env.example` to `.env` and put your
   key there. `.env` is listed in `.gitignore`, so it is never committed.

   ```bash
   cp .env.example .env
   ```

   Generating questions and grading freeform answers need a key. Everything
   else works offline against `data/questions.json`.

3. **Run it:**

   ```bash
   python main.py
   ```

## Running the tests

```bash
python -m pytest
```

The tests never call the real API: the OpenAI SDK is mocked. They cover
error handling (authentication failure, rate limits, network errors, model
refusals), question validation, the response schemas, prompt building,
weighted selection, persistence, and the statistics table.

## Evaluating the prompts

`evals/cases.json` holds a small, repeatable set of grading and
question-generation cases, including a prompt-injection attempt. After
changing a prompt, bump `PROMPT_VERSION` in `prompts.py` and run:

```bash
python -m scripts.run_evals
```

This calls the real API (a few cents) and prints a pass/fail table.

## Project layout

```
learning_companion/
├── main.py                      # Entry point: python main.py
├── pyproject.toml               # Dependencies, Python version, pytest settings
├── learning_companion/
│   ├── config.py                # Loads the API key and settings from .env
│   ├── models.py                # Question dataclass
│   ├── schemas.py               # Pydantic shapes for the LLM's replies
│   ├── prompts.py               # Versioned prompt templates
│   ├── llm_client.py            # All OpenAI calls and error handling
│   ├── quiz_manager.py          # Selection, grading and scoring logic
│   ├── storage.py               # Saves questions and test results
│   └── cli/                     # One small file per menu feature
│       ├── app.py               # Menu loop
│       ├── terminal.py          # Shared Rich console and input helpers
│       ├── generate.py          # 1) Generate Questions
│       ├── stats.py             # 2) View Statistics
│       ├── quiz.py              # 3) Practice Mode and 4) Test Mode
│       └── manage.py            # 5) Manage Questions
├── tests/                       # Unit tests (no network, no API key)
├── evals/cases.json             # Prompt evaluation cases
├── scripts/run_evals.py         # Runs the evaluation cases against the real API
└── data/
    ├── questions.json           # Question bank (sample data included)
    └── results.txt              # Test-mode score log
```

## How it works

- **Structured Outputs.** `llm_client.py` sends each request with a Pydantic
  schema from `schemas.py`, so the model must reply in exactly that shape and
  the OpenAI SDK returns a parsed object. There is no hand-written JSON
  parsing. A small `is_usable()` check then drops questions whose content
  doesn't make sense, such as a multiple-choice answer that isn't one of the
  options.
- **One error type.** Authentication failures, rate limits, network errors,
  model refusals and empty replies all become a single `LLMError` with a
  readable message, so the rest of the app never imports `openai`.
- **Failed grading is not a wrong answer.** If the LLM can't grade a
  freeform answer, the attempt is not recorded, so your statistics stay
  accurate.
- **Prompt-injection guard.** The grading prompt puts the student's answer
  inside `<student_answer>` tags and tells the model to treat it as text to
  grade, never as instructions.
- **Separated layers.** `QuizManager` holds the logic and never prints or
  reads input; the `cli/` package handles the terminal. This keeps the logic
  easy to test and each file short.

---

## Previous exercise repository

Link to the public GitHub repository for the previous hands-on exercise:
**[TODO: paste the link to your previous exercise's repository here]**
