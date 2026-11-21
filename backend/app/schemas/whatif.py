from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class WhatIfRequest(BaseModel):
    tenth_pct: Optional[float] = None
    twelfth_pct: Optional[float] = None
    cgpa: Optional[float] = None
    skills: Optional[List[str]] = None
    skill_mode: str = "AND"  # AND / OR
    years_experience: Optional[float] = None
    location: Optional[str] = None
    grad_year: Optional[int] = None
    min_match_score: Optional[float] = None
    jd_id: Optional[int] = None

class FunnelStage(BaseModel):
    filter: str
    before: int
    after: int
    removed: int
    percentage_removed: float

class NearMissCandidate(BaseModel):
    candidate_id: int
    name: str
    failed_filter: str
    actual: Any
    required: Any
    gap: float
    total_failures: int
    match_score: Optional[float] = None

class HighMatchRemovedCandidate(BaseModel):
    candidate_id: int
    name: str
    match_score: float
    failed_filters: List[str]
    details: Dict[str, Any]

class RelaxationSuggestion(BaseModel):
    filter_name: str
    current_value: Any
    suggested_value: Any
    description: str
    recovered_count: int
    field_key: str

class WhatIfResponse(BaseModel):
    total_candidates: int
    passing_candidates: int
    removed_candidates: int
    filters: List[FunnelStage]
    high_match_removed: List[HighMatchRemovedCandidate]
    near_miss_candidates: List[NearMissCandidate]
    relaxation_suggestions: List[RelaxationSuggestion]
