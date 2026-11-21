from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class EvidenceBase(BaseModel):
    field_name: str
    value: Optional[str] = None
    confidence: str = "medium"
    source_text: Optional[str] = None
    human_verified: bool = False

class EvidenceResponse(EvidenceBase):
    id: int
    candidate_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AuditLogResponse(BaseModel):
    id: int
    candidate_id: int
    from_stage: Optional[str] = None
    to_stage: str
    changed_by: str
    changed_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MatchBreakdown(BaseModel):
    skills_score: float
    max_skills_score: float = 50.0
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    experience_score: float
    max_experience_score: float = 25.0
    candidate_experience: float
    required_experience: float
    education_score: float
    max_education_score: float = 15.0
    degree: Optional[str] = None
    tfidf_score: float
    max_tfidf_score: float = 10.0

class CandidateBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    college: Optional[str] = None
    degree: Optional[str] = None
    grad_year: Optional[int] = None
    tenth_pct: Optional[float] = None
    twelfth_pct: Optional[float] = None
    cgpa_10: Optional[float] = None
    years_experience: float = 0.0
    resume_filename: Optional[str] = None
    resume_text: Optional[str] = None
    pipeline_stage: str = "Applied"

class CandidateCreate(CandidateBase):
    pass

class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    college: Optional[str] = None
    degree: Optional[str] = None
    grad_year: Optional[int] = Field(None, ge=1970, le=2040)
    tenth_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    twelfth_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    cgpa_10: Optional[float] = Field(None, ge=0.0, le=10.0)
    years_experience: Optional[float] = Field(None, ge=0.0)
    skills: Optional[List[str]] = None

class CandidateStageUpdate(BaseModel):
    stage: str

class VerifyEvidenceRequest(BaseModel):
    field_name: str
    value: Optional[str] = None
    confirmed: bool = True

class CandidateResponse(CandidateBase):
    id: int
    created_at: datetime
    updated_at: datetime
    evidence_fields: List[EvidenceResponse] = []
    match_score: Optional[float] = None
    match_breakdown: Optional[MatchBreakdown] = None
    needs_review: bool = False
    skills: List[str] = []
    model_config = ConfigDict(from_attributes=True)

class PaginatedCandidateResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[CandidateResponse]

class JobDescriptionBase(BaseModel):
    title: str
    description: str
    min_experience: float = 0.0
    required_skills: str
    nice_to_have_skills: Optional[str] = None

class JobDescriptionCreate(BaseModel):
    title: Optional[str] = None
    raw_text: str

class JobDescriptionResponse(JobDescriptionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class StatsResponse(BaseModel):
    total_candidates: int
    applied: int
    shortlisted: int
    interview: int
    offers: int
    rejected: int
    total_jds: int
    average_jd_match: float = 0.0
    candidates_with_confidence_issues: int = 0
    candidates_requiring_review: int = 0
    fields_needing_verification: int = 0
