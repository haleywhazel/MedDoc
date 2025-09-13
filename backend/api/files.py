from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from backend import ROOT_DIR

router = APIRouter(tags=["files"])


@router.get("/pdf")
async def get_pdf(file: str = Query(..., description="PDF filename")) -> FileResponse:  # noqa: D401
    """Stream a PDF sitting under local/.

    We accept only base filenames to avoid directory traversal.
    """
    filename = Path(file).name
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    pdf_path = ROOT_DIR / "local" / filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=pdf_path, media_type="application/pdf", filename=filename)
