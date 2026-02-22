"""Pydantic models for the Seasaw TrustScore API."""

from datetime import datetime
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Incoming request — just a search query."""
    query: str = Field(..., min_length=1, max_length=200, examples=["netflix"])


class ServiceInfo(BaseModel):
    """Result of LLM service resolution (call #1)."""
    service_name: str
    domain: str
    terms_url: str
    privacy_url: str


class PolicyAttribute(BaseModel):
    """A single extracted policy attribute."""
    id: str
    label: str
    value: str
    severity: str = Field(..., pattern=r"^(good|neutral|bad)$")
    evidence: str
    weight: int
    points_earned: float


class AnalyzeResponse(BaseModel):
    """Full analysis result returned to the frontend."""
    service_name: str
    domain: str
    terms_url: str
    privacy_url: str
    trust_score: int = Field(..., ge=0, le=100)
    grade: str
    analyzed_at: str
    attributes: list[PolicyAttribute]
    error: str | None = None
