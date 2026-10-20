"""Loads configuration (API key, model name, file paths) from the environment.

Values are read from real environment variables first; if a `.env` file exists
and python-dotenv is installed, it is loaded first so its values populate the
environment too. This keeps secrets out of source control (see .gitignore).
"""

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is optional; real environment variables still work.
    pass

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
QUESTIONS_FILE = os.environ.get("QUESTIONS_FILE", "data/questions.json")
RESULTS_FILE = os.environ.get("RESULTS_FILE", "data/results.txt")
