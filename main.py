import asyncio
import json
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from config import settings
from models.schemas import AuditRequest
from core.parser import parse_resume
from core.auditor import run_audit
from core.verifier import verify_verdict
from core.db import get_db, engine, Base
from models.db_models import AuditRecord

log = structlog.get_logger()

BASE_DIR = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="FitAuditor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


def require_api_token(authorization: str = Header(default="")):
    expected = f"Bearer {settings.api_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API token.")


@app.get("/")
async def root():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/scenario")
async def get_scenario():
    resume = (BASE_DIR / "data" / "sample_resume.txt").read_text()
    jd = (BASE_DIR / "data" / "sample_jd.txt").read_text()
    return {"resume": resume, "jd": jd}


def _sse(event_type: str, data: dict) -> str:
    return f"data: {json.dumps({'event_type': event_type, 'data': data})}\n\n"


@app.post("/api/audit", dependencies=[Depends(require_api_token)])
async def audit(req: AuditRequest, db: AsyncSession = Depends(get_db)):
    async def stream():
        line_blocks = parse_resume(req.resume_text)
        line_map = {b.id: b.text for b in line_blocks}

        yield _sse("PARSED", {"lines": [b.dict() for b in line_blocks]})
        await asyncio.sleep(0.2)

        try:
            verdicts = await run_audit(req.jd_text, line_blocks)
        except Exception:
            log.error("audit_failed", exc_info=True)
            yield _sse("ERROR", {"message": "The audit could not be completed. Please try again."})
            return

        matched_score = 0.0
        risk_flags = 0
        final_verdicts = []

        for raw_verdict in verdicts:
            verdict = verify_verdict(raw_verdict, line_map)
            final_verdicts.append(verdict)

            if verdict["status"] == "MATCHED":
                matched_score += 1
            elif verdict["status"] == "PARTIAL":
                matched_score += 0.5
            if verdict["status"] == "UNVERIFIED":
                risk_flags += 1

            yield _sse("VERDICT", verdict)
            await asyncio.sleep(0.45)

        total = len(verdicts) or 1
        fit_score = round((matched_score / total) * 100)
        verified = len(verdicts) - risk_flags

        record = AuditRecord(
            resume_text=req.resume_text,
            jd_text=req.jd_text,
            fit_score=fit_score,
            total_requirements=len(verdicts),
            risk_flags=risk_flags,
            verified=verified,
            verdicts=final_verdicts,
        )
        db.add(record)
        await db.commit()

        log.info("audit_completed", audit_id=record.id, fit_score=fit_score, risk_flags=risk_flags)

        yield _sse("SUMMARY", {
            "id": record.id,
            "fit_score": fit_score,
            "total_requirements": len(verdicts),
            "risk_flags": risk_flags,
            "verified": verified,
        })

    return StreamingResponse(stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)