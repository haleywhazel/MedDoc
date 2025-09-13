from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from backend.api.chat import router as chat_router
from backend.api.files import router as files_router

app = FastAPI(
    title="MedDoc HR Assistant",
    description="AI chatbot for hospital HR queries",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS – allow Next.js dev server (localhost:3000) and any additional origins
# configured via the MEDDOC_CORS_ORIGINS env variable (comma-separated).
# ---------------------------------------------------------------------------
import os

cors_origins_env = os.getenv("MEDDOC_CORS_ORIGINS")
allow_origins = ["http://localhost:3000"]
if cors_origins_env:
    allow_origins.extend(o.strip() for o in cors_origins_env.split(",") if o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")
app.include_router(files_router, prefix="/api")


@app.get("/", tags=["health"])
async def health() -> dict[str, str]:
    """Simple health-check endpoint."""
    return {"status": "ok"} 