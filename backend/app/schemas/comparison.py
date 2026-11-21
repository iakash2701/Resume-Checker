from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class CandidateCompareRequest(BaseModel):
    candidate_ids: List[int]
    jd_id: Optional[int] = None

class RadarDimension(BaseModel):
    dimension: str
    scores: Dict[str, float]  # e.g. {"Candidate A": 85.0, "Candidate B": 72.0}

class CandidateComparisonCard(BaseModel):
    candidate_id: int
    name: str
    location: Optional[str] = None
    degree: Optional[str] = None
    college: Optional[str] = None
    tenth_pct: Optional[float] = None
    twelfth_pct: Optional[float] = None
    cgpa_10: Optional[float] = None
    years_experience: float = 0.0
    grad_year: Optional[int] = None
    skills: List[str] = []
    pipeline_stage: str = "Applied"
    jd_match_score: Optional[float] = None
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    unique_skills: List[str] = []
    shared_skills: List[str] = []
    confidence_issues: List[str] = []
    is_verified: bool = False
    normalized_scores: Dict[str, float] = {}  # skills, experience, education, jd_match on 0-100

class CandidateCompareResponse(BaseModel):
    candidates: List[CandidateComparisonCard]
    radar_data: List[Dict[str, Any]]  # format for Recharts: [{"subject": "Skills", "Cand1": 80, "Cand2": 90}, ...]
    verdict: str
    shared_skills: List[str]
    relative_strengths: Dict[str, str]

class FilterPresetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    filters_json: str

class FilterPresetCreate(FilterPresetBase):
    pass

class FilterPresetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    filters_json: Optional[str] = None

class FilterPresetResponse(FilterPresetBase):
    id: int
    created_at: Any
    updated_at: Any
    model_config = ConfigDict(from_attributes=True)
