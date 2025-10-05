from __future__ import annotations

import os
from typing import Any, Dict, Tuple, Optional, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.retrieval.retrieval import _extract_answer_and_sources, get_answer

router = APIRouter(tags=["chat"])


class QueryRequest(BaseModel):
    question: str
    history: Optional[List[dict]] = Field(
        default=None,
        description="Previous conversation history"
    )

class Source(BaseModel):
    file: str
    page: int | None = None
    text: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]


_DUMMY_ANSWER = 'During maternity leave, employees working full or part-time will be entitled to occupational maternity pay as follows:\n- For the first eight weeks, full pay less any Statutory Maternity Pay or maternity allowance\n- For the next 18 weeks, half pay plus any Statutory Maternity Pay or maternity allowance (total cannot exceed full pay)\n- For the next 13 weeks, Statutory Maternity Pay or maternity allowance\n- For the final 13 weeks, no pay.'
_DUMMY_ANSWER += '{"sources":[{"file":"Managers-and-Staff-Policy-Handbook-2024-W100.pdf","page":40},{"file":"W19-Leave-Policy-Chapter-6-Shared-Parental-Leave-Procedure-Amends-April-2024-V3.pdf","page":6},{"file":"W19-Leave-Policy-Chapter-4-Fertility-Pregnancy-and-Maternity-Additions-to-App-C-Dec-2024-V2.1.pdf","page":7}]}'

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

# ---------------------------------------------------------------------------
# Main chat route – returns answer + source metadata
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=QueryResponse)
async def chat(req: QueryRequest, use_dummy_response: bool = Query(False)) -> QueryResponse:  # noqa: D401
    """Return an answer for a staff HR question.

    Set query param `use_dummy_response=true` to return a hard-coded dummy answer (UI testing).
    """
    if use_dummy_response:
        answer, sources = _extract_answer_and_sources(_DUMMY_ANSWER)
        return QueryResponse(answer=_DUMMY_ANSWER, sources=sources)

    # Use real pipeline with tracing so we can extract source metadata
    answer, sources, trace = get_answer(req.question, history=req.history, trace=True)
    return QueryResponse(answer=answer, sources=[Source(**s) for s in sources])


# ---------------------------------------------------------------------------
# Debug route – returns the full trace alongside the answer
# ---------------------------------------------------------------------------


class DebugResponse(BaseModel):
    answer: str
    trace: Dict[str, Any]
    sources: list[Source]


@router.post("/chat/debug", response_model=DebugResponse)
async def chat_debug(req: QueryRequest, use_dummy_response: bool = Query(False)) -> DebugResponse:  # noqa: D401
    """Same as `/chat` but also returns the retrieval & generation trace."""
    if use_dummy_response:
        answer, sources = _extract_answer_and_sources(_DUMMY_ANSWER)
        return DebugResponse(answer=answer, trace=_DUMMY_TRACE, sources=sources)

    answer, sources, trace = get_answer(req.question, trace=True)
    return DebugResponse(answer=answer, trace=trace, sources=[Source(**s) for s in sources])
