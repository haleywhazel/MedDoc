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




_DUMMY_ANSWER = "This is a dummy answer (frontend testing mode). Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
_DUMMY_TRACE = {
    "question": "Dummy question",
    "retrieved_docs": [
        {
            "page_content": "Policy implementation:\n\nAdoption leave is the period of absence from work before and after the adoption of a child. A ‘matching certificate’ from the adoption agency is evidence of the entitlement to take Adoption Leave. Employees must notify the manager in writing using the Adoption Leave Form within 7 days of being notified by the adoption agency having been matched with a child for adoption or by the 15th week before the baby’s due date if applying via a surrogacy arrangement. Employees are entitled to take 52 weeks’ adoption leave. Employees are required to give at least 8 weeks’ notice if they wish to return to work before the agreed return date.",
            "metadata": {
                "filename": "Managers-and-Staff-Policy-Handbook-2024-W100.pdf",
                "page_number": 37,
                "pdf_hash": "c7ed49dd143740536120374bc7ba05b76e00ab485358346c33195b1032fe79e1",
            },
        },
        {
            "page_content": "You can choose to start your leave either on the date of the child’s placement (whether this is earlier or later than expected), or from a fixed date which can be up to 14 days before the expected date of placement. If the placement is delayed and Adoption Leave has commenced, it cannot be stopped and resumed again at a later date. Leave can start on any day of the week\n\n17. Can I change my mind about the date I want my leave to start? You can change your mind about the date on which you wish to start your Adoption Leave provided you advise your Manager at least 28 days in advance (unless this is not reasonably practicable).\n\nStatutory Adoption Leave\n\n18. If I am not eligible for Occupational Adoption Pay can I claim statutory adoption pay? The handbook states in section 15.102 that:",
            "metadata": {
                "page_number": 5,
                "pdf_hash": "45ca58270db5708d0be625c6f28f24bf5c1541e94c3ebb741a03978314f8e419",
                "filename": "W19-Leave-Policy-Chapter-1-Adoption-Leave-Procedure-Amends-April-2024-v2.pdf",
            },
        },
        {
            "page_content": "Adopting from overseas to qualify employees must inform the manager within 28 days of the official notification and the date the child will arrive in GB.\n\nFoster parents who are subsequently matched for adoption, will be entitled to adoption leave when the child is actually placed with them for adoption.\n\nAdopting more than one child: Only one period of Adoption leave can be taken irrespective of whether more than one child is placed for adoption.\n\nThe adoption does not take place: Employees must return to work within a reasonable period of time by agreement with their manager. Also, if the adoption terminates i.e. (“Be disrupted”) the employee will be entitled to continue their adoption leave and receive the appropriate payment for that time.\n\n37",
            "metadata": {
                "filename": "Managers-and-Staff-Policy-Handbook-2024-W100.pdf",
                "pdf_hash": "c7ed49dd143740536120374bc7ba05b76e00ab485358346c33195b1032fe79e1",
                "page_number": 37,
            },
        },
    ],
    "prompt": "Dummy prompt",
    "raw_llm_response": _DUMMY_ANSWER,
    "final_answer": _DUMMY_ANSWER,
    "num_tokens": 0,
    "ts": "2025-01-01T00:00:00Z",
}


from fastapi import Query


@router.post("/chat", response_model=QueryResponse)
async def chat(req: QueryRequest, use_dummy_response: bool = Query(False)) -> QueryResponse:  # noqa: D401
    """Return an answer for a staff HR question.

    Set query param `use_dummy_response=true` to return a hard-coded dummy answer (UI testing).
    """
    if use_dummy_response:
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
async def chat_debug(req: QueryRequest, use_dummy_response: bool = Query(False)) -> DebugResponse:  # noqa: D401
    """Same as `/chat` but also returns the retrieval & generation trace."""
    if use_dummy_response:
        return DebugResponse(answer=_DUMMY_ANSWER, trace=_DUMMY_TRACE)
    answer, trace = get_answer(req.question, trace=True)
    return DebugResponse(answer=answer, trace=trace)
