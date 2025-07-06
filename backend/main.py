from fastapi import FastAPI

from backend.api.chat import router as chat_router

app = FastAPI(
    title="MedDoc HR Assistant",
    description="AI chatbot for hospital HR queries",
    version="0.1.0",
)

app.include_router(chat_router, prefix="/api")


@app.get("/", tags=["health"])
async def health() -> dict[str, str]:
    """Simple health-check endpoint."""
    return {"status": "ok"} 