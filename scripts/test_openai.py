from __future__ import annotations

"""Quick diagnostic script to verify your OPENAI_API_KEY is set correctly.

Usage (from project root):

    python scripts/test_openai.py

It will print a short assistant response if the key is valid; otherwise you
will see an authentication error from the OpenAI client.
"""

import os
import sys
import typing as _t
from pathlib import Path

from openai import OpenAI

# ---------------------------------------------------------------------------
# Ensure project root is importable when running the script directly
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load env vars via backend.config (which already calls python-dotenv)
from backend.config import OPENAI_API_KEY, OPENAI_MODEL, require_env


def main() -> None:
    # Ensure the key is present and assign it to the openai client
    assistant_reply: str = ""
    try:
        client = OpenAI(api_key=require_env("OPENAI_API_KEY", OPENAI_API_KEY))
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "user", "content": "Hello, OpenAI! Write a haiku about cats for me."}
            ],
            max_tokens=5,
        )
        assistant_reply = str(completion.choices[0].message.content).strip()
    except Exception as exc:  # noqa: BLE001
        print("Error calling OpenAI:", exc, file=sys.stderr)
        sys.exit(1)

    print("OpenAI response:", assistant_reply)


if __name__ == "__main__":
    main() 
