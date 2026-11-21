from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DuplicateMatch(BaseModel):
    candidate_id: int
    name: str
    email: Optional[str] = None
    college: Optional[str] = None
    similarity_score: float
    classification: str
    reasons: List[str]

class DuplicateCheckResponse(BaseModel):
    candidate_id: int
    has_duplicates: bool
    duplicate_count: int
    matches: List[DuplicateMatch]

class DuplicateMarkRequest(BaseModel):
    duplicate_of_id: int

class SkillGapResponse(BaseModel):
    total_required: int
    matched_required: List[str]
    missing_required: List[str]
    matched_nice: List[str]
    missing_nice: List[str]
    skill_coverage_pct: float
    all_candidate_skills: List[str]

class EvidenceItem(BaseModel):
    skill: str
    status: str
    confidence: str
    source_type: str
    evidence_snippet: str
    interview_probe: str

class EvidenceGraphNode(BaseModel):
    label: str
    detail: str
    type: str

class EvidenceGraphChain(BaseModel):
    skill: str
    status: str
    nodes: List[EvidenceGraphNode]

class HiringIntelligenceResponse(BaseModel):
    evidence_score: float
    evidence_items: List[EvidenceItem]
    strong_evidence: List[str]
    weak_evidence: List[str]
    missing_evidence: List[str]
    evidence_graph: List[EvidenceGraphChain]

class BulkEmailCandidateItem(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    skills: Optional[str] = ""

class BulkEmailRequest(BaseModel):
    candidates: List[BulkEmailCandidateItem]
    template_key: str = "interview_invitation"
    role: str = "Software Engineer"
    dry_run: bool = True
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None

class EmailQueueItem(BaseModel):
    candidate_id: Optional[int] = None
    candidate_name: str
    to_email: str
    subject: str
    body: str
    status: str
    delivered: bool
    dry_run: bool

class BulkEmailResponse(BaseModel):
    mode: str
    smtp_configured: bool
    total_queued: int
    total_delivered: int
    queue: List[EmailQueueItem]
