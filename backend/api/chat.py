from __future__ import annotations

from typing import Any, Dict, Tuple

from fastapi import APIRouter
from pydantic import BaseModel

from backend.retrieval.retrieval import get_answer

router = APIRouter(tags=["chat"])


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str


@router.post("/chat", response_model=QueryResponse)
async def chat(req: QueryRequest) -> QueryResponse:  # noqa: D401
    """Return an answer for a staff HR question."""
    answer = get_answer(req.question)
    return QueryResponse(answer=answer)


# ---------------------------------------------------------------------------
# Debug route – returns the full trace alongside the answer
# ---------------------------------------------------------------------------


class DebugResponse(BaseModel):
    answer: str
    trace: Dict[str, Any]


@router.post("/chat/debug", response_model=DebugResponse)
async def chat_debug(req: QueryRequest) -> DebugResponse:  # noqa: D401
    """Same as `/chat` but also returns the retrieval & generation trace."""
    answer, trace = get_answer(req.question, trace=True)
    # `trace` is already a plain dict (see retrieval.get_answer)
    return DebugResponse(answer=answer, trace=trace)