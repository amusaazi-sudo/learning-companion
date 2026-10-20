# AI-Powered Learning Companion

A command-line study tool that uses an LLM (OpenAI's API) to generate quiz
questions on any topic, evaluate freeform answers, and track your progress
over time via weighted practice and randomized tests.

## Features

- **Generate Questions (LLM)** — enter a topic, get a mix of MCQ + freeform
  questions from the LLM, review/edit/accept each one before it's saved.
- **View Statistics** — see every saved question: ID, active status, topic,
  type, source (LLM/Manual), times shown, and correct-answer percentage.
- **Practice Mode** — endless practice with *weighted* question selection:
  questions you get wrong more often show up more often; ones you've
  mastered fade into the background.
- **Test Mode** — pick how many questions you want, answered once each with
  no repeats, final score is printed and appended to `data/results.txt`.
- **Manage Questions** — list all questions, or enable/disable a specific
  question by ID (with a confirmation step showing the question first).
  Disabled questions never appear in Practice or Test mode.

## Project layout

```
learning_companion/
├── main.py                        # CLI entry point / menu loop
├── learning_companion/
│   ├── models.py                  # Question dataclass (OOP model)
│   ├── llm_client.py              # LLMClient: all OpenAI API calls + error handling
│   ├── quiz_manager.py            # QuizManager: selection/evaluation/scoring logic
│   ├── storage.py                 # QuestionStore + ResultsLog: file persistence
│   └── config.py                  # Loads API key / settings from environment
├── tests/                         # Unit tests (no network calls required)
├── data/
│   ├── questions.json             # Persisted question bank (sample data included)
│   └── results.txt                # Append-only test-mode score log
├── requirements.txt
├── .env.example                   # Template for your local .env (never committed)
└── .gitignore                     # Excludes .env, __pycache__, venvs, etc.
```

## Setup

1. **Clone the repo and install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Provide your OpenAI API key.** Copy `.env.example` to `.env` and fill
   in your key (or just export it as a real environment variable):

   ```bash
   cp .env.example .env
   # then edit .env and set OPENAI_API_KEY=sk-...
   ```

   The key is never hardcoded and `.env` is listed in `.gitignore`, so it
   won't be committed. `Generate Questions`, `Practice Mode`, and
   `Test Mode` (for freeform questions) all require a valid key; every
   other mode works fully offline against the local `data/questions.json`.

3. **Run it:**

   ```bash
   python main.py
   ```

## How the pieces fit together (OOP overview)

- `Question` (`models.py`) — a dataclass holding one question's text, type,
  options, correct answer, active flag, and running stats. Exposes
  `correct_percentage` and `is_mcq` as computed properties, plus
  `record_attempt()` / `set_active()` mutators and `to_dict()`/`from_dict()`
  for JSON persistence.
- `LLMClient` (`llm_client.py`) — wraps all calls to the OpenAI Chat
  Completions API. `generate_questions()` prompts the model for strict JSON
  and parses/validates it into plain dicts; `evaluate_freeform()` sends the
  question, reference answer, and user answer, and parses a `{"verdict":
  ..., "explanation": ...}` JSON judgment. All network/auth/rate-limit
  failures are caught and re-raised as a single `LLMError` so the rest of
  the app never has to know about `openai`-specific exceptions.
- `QuestionStore` / `ResultsLog` (`storage.py`) — read/write
  `data/questions.json` and append lines to `data/results.txt`.
- `QuizManager` (`quiz_manager.py`) — the orchestrator. Holds the in-memory
  list of `Question` objects, talks to `LLMClient` only when needed
  (lazily, so unit tests never require an API key), and implements the
  selection/evaluation logic:
  - `compute_weight()` / `weighted_choice()` — pure functions implementing
    the weighted-random Practice mode selection (higher weight for unseen
    or frequently-missed questions).
  - `pick_test_questions()` — random sample without replacement for Test
    mode.
  - `evaluate_mcq()` — direct string comparison.
  - `evaluate_freeform()` — delegates to the LLM, degrades gracefully to
    "incorrect + explanation" if the API call fails.
- `main.py` — thin CLI layer: menu loop + `input()`/`print()` for each of
  the five modes, all glued together through a single `QuizManager`
  instance.

## Running the tests

```bash
python -m unittest discover -s tests -v
```

The test suite (`tests/test_models.py`, `tests/test_quiz_manager.py`,
`tests/test_storage.py`) covers MCQ evaluation, the weighted-selection
logic, enable/disable persistence, and JSON save/load round-tripping —
none of it requires network access or an API key.

## Notes on error handling

`LLMClient` catches `AuthenticationError`, `RateLimitError`,
`APIConnectionError`, and generic `APIError` from the OpenAI SDK and
re-raises them as a single `LLMError` with a human-readable message, which
`main.py` catches and prints without crashing the program. Freeform
evaluation failures during Practice/Test mode are treated as "could not
verify" rather than silently crashing the session.

---

## Previous exercise repository

Link to the public GitHub repository for the previous hands-on exercise:
**[TODO: paste the link to your previous exercise's repository here]**
