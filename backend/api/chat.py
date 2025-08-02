from __future__ import annotations

import os
from typing import Any, Dict, Tuple

from fastapi import APIRouter
from pydantic import BaseModel

from backend.retrieval.retrieval import get_answer

router = APIRouter(tags=["chat"])


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str


USE_DUMMY = os.getenv("MEDDOC_DUMMY_RESPONSES") == "1"

_DUMMY_ANSWER = "This is a dummy answer (frontend testing mode). Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
_DUMMY_TRACE = {
    "question": "Dummy question",
    "retrieved_docs": [],
    "prompt": "Dummy prompt",
    "raw_llm_response": _DUMMY_ANSWER,
    "final_answer": _DUMMY_ANSWER,
    "num_tokens": 0,
    "ts": "2025-01-01T00:00:00Z",
}


@router.post("/chat", response_model=QueryResponse)
async def chat(req: QueryRequest) -> QueryResponse:  # noqa: D401
    """Return an answer for a staff HR question."""
    if USE_DUMMY:
        return QueryResponse(answer=_DUMMY_ANSWER)
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
    if USE_DUMMY:
        return DebugResponse(answer=_DUMMY_ANSWER, trace=_DUMMY_TRACE)
    answer, trace = get_answer(req.question, trace=True)
    return DebugResponse(answer=answer, trace=trace)
