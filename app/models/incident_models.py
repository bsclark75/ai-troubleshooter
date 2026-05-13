from pydantic import BaseModel
from typing import Optional


class AnalysisResponse(BaseModel):

    root_cause: str
    recommended_fix: str


class KnownIssue(BaseModel):

    issue: str
    cause: str
    fix: str


class SimilarIncident(BaseModel):

    incident_id: str
    severity: str
    analysis: dict


class IncidentResponse(BaseModel):

    incident_id: str
    severity: str
    known_issue: Optional[KnownIssue] = None
    similar_incident: Optional[SimilarIncident] = None
    analysis: AnalysisResponse