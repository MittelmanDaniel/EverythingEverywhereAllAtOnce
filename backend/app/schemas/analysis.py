from pydantic import BaseModel


class PathNotTakenResponse(BaseModel):
    id: str
    category: str
    title: str
    description: str
    evidence_json: str
    source_service: str
    confidence: float
    timeline_date: str | None


class AnalysisResponse(BaseModel):
    paths: list[PathNotTakenResponse]
    status: str  # "pending", "collecting", "ready"
