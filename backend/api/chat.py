from fastapi import APIRouter
from pydantic import BaseModel

from backend.retrieval.retrieval import get_answer

router = APIRouter(tags=["chat"])


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str


@router.post("/chat", response_model=QueryResponse)
async def chat(req: QueryRequest) -> QueryResponse:
    """Return an answer for a staff HR question."""
    answer = get_answer(req.question)
    return QueryResponse(answer=answer) 