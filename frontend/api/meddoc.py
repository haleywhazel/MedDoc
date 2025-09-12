"""Serverless entrypoint for MedDoc FastAPI app on Vercel."""
import pathlib
import sys

from mangum import Mangum

# Ensure the monorepo root (which contains `backend/`) is on PYTHONPATH
repo_root = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(repo_root))

from backend.main import app as fastapi_app  # noqa: E402

# Vercel will invoke this handler for each request
handler = Mangum(fastapi_app)
