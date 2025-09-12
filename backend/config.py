from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from backend import ROOT_DIR

# Load variables from a `.env` file if present (noop in production where env vars are set by the platform).
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)

# Core secrets / settings
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

# Model selection
# OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Other knobs
CHROMA_PATH: str = os.getenv("CHROMA_PATH", f"{ROOT_DIR}/chroma_langchain_db")


def require_env(var_name: str, value: str | None) -> str:
    """Raise a clear exception when a required variable is missing."""
    if not value:
        raise RuntimeError(
            f"Required environment variable '{var_name}' is not set. "
            "Create a .env file (see env.example) or configure it in your deployment environment."
        )
    return value 