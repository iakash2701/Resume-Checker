import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class ConfidenceLevel(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    email = Column(String(255), index=True, nullable=True)
    phone = Column(String(50), index=True, nullable=True)
    location = Column(String(255), index=True, nullable=True)
    college = Column(String(255), index=True, nullable=True)
    degree = Column(String(255), index=True, nullable=True)
    grad_year = Column(Integer, index=True, nullable=True)
    tenth_pct = Column(Float, index=True, nullable=True)
    twelfth_pct = Column(Float, index=True, nullable=True)
    cgpa_10 = Column(Float, index=True, nullable=True)
    years_experience = Column(Float, default=0.0, index=True)
    resume_filename = Column(String(255), nullable=True)
    resume_text = Column(Text, nullable=True)
    pipeline_stage = Column(String(50), default="Applied", index=True)
    is_duplicate = Column(Boolean, default=False, index=True)
    duplicate_of_id = Column(Integer, ForeignKey("candidates.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    evidence_fields = relationship("CandidateFieldEvidence", back_populates="candidate", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="candidate", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_candidate_academic", "tenth_pct", "twelfth_pct", "cgpa_10"),
        Index("idx_candidate_exp_grad", "years_experience", "grad_year"),
    )

class CandidateFieldEvidence(Base):
    __tablename__ = "candidate_field_evidence"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    value = Column(String(255), nullable=True)
    confidence = Column(String(20), default=ConfidenceLevel.medium.value)
    source_text = Column(Text, nullable=True)
    human_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="evidence_fields")

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    min_experience = Column(Float, default=0.0, index=True)
    required_skills = Column(Text, nullable=False)  # JSON or comma-delimited string
    nice_to_have_skills = Column(Text, nullable=True) # JSON or comma-delimited string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    from_stage = Column(String(50), nullable=True)
    to_stage = Column(String(50), nullable=False)
    changed_by = Column(String(100), default="system")
    changed_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="audit_logs")

class FilterPreset(Base):
    __tablename__ = "filter_presets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    filters_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
