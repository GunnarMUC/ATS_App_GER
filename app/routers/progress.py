from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import JobDescription

router = APIRouter(tags=["progress"])


@router.get("/jobs/{job_id}/progress")
async def job_progress(job_id: str, db: Session = Depends(get_db)):
    async def event_stream():
        steps = [
            "Stelle lesen",
            "Rolle erkennen",
            "Plan bauen",
            "CV schreiben",
            "prüfen",
        ]
        job = db.get(JobDescription, job_id)
        for i, step in enumerate(steps):
            payload = {
                "job_id": job_id,
                "step": step,
                "index": i,
                "total": len(steps),
                "generating": bool(job.generating) if job else False,
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.05)
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
