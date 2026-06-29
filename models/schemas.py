from datetime import datetime
from pydantic import BaseModel
from typing import Literal, Optional


class AuditRequest(BaseModel):
    resume_text: str
    jd_text: str


class LineBlock(BaseModel):
    id: str
    text: str


class Verdict(BaseModel):
    requirement: str
    status: Literal["MATCHED", "PARTIAL", "GAP", "UNVERIFIED"]
    evidence_line_ids: list[str]
    confidence: float
    rationale: str
    verification_note: Optional[str] = None


class AuditSummary(BaseModel):
    id: str
    created_at: datetime
    fit_score: int
    total_requirements: int
    risk_flags: int
    verified: int