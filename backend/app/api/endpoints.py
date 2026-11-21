from app.services.resume_parser import parse_resume
import math
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status, Response, UploadFile, File
import tempfile
import os
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_
from typing import List, Optional
import json

from app.database import get_db
from app.models import Candidate, JobDescription, CandidateFieldEvidence, AuditLog, FilterPreset
from app.schemas import (
    CandidateResponse,
    CandidateUpdate,
    CandidateStageUpdate,
    VerifyEvidenceRequest,
    AuditLogResponse,
    PaginatedCandidateResponse,
    JobDescriptionResponse,
    JobDescriptionCreate,
    StatsResponse
)
from app.schemas.whatif import WhatIfRequest, WhatIfResponse
from app.schemas.comparison import (
    CandidateCompareRequest,
    CandidateCompareResponse,
    FilterPresetCreate,
    FilterPresetUpdate,
    FilterPresetResponse
)
from app.services.whatif_service import evaluate_whatif_funnel
from app.services.comparison_service import compare_candidates_service
from app.services.export_service import generate_candidates_csv
from app.services.jd_service import parse_job_description_text
from app.services.matching_service import compute_candidate_match
from app.services.skills_service import (
    normalize_skill,
    extract_skills_from_text,
    expand_skills_with_implications
)
from app.schemas.phase7 import (
    DuplicateCheckResponse,
    DuplicateMarkRequest,
    SkillGapResponse,
    HiringIntelligenceResponse,
    BulkEmailRequest,
    BulkEmailResponse
)
from app.services.dedup_service import find_duplicates_for_candidate
from app.services.intelligence_service import analyze_skill_gap, analyze_hiring_intelligence
from app.services.email_service import process_bulk_email_queue, EMAIL_TEMPLATES

router = APIRouter()

VALID_STAGES = {"Applied", "Shortlisted", "Interview", "Offer", "Rejected"}

@router.post("/candidates/compare", response_model=CandidateCompareResponse)
def compare_candidates(payload: CandidateCompareRequest, db: Session = Depends(get_db)):
    try:
        return compare_candidates_service(payload.candidate_ids, payload.jd_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/candidates/export", response_class=PlainTextResponse)
def export_candidates_csv(
    tenth_min: Optional[float] = Query(None),
    twelfth_min: Optional[float] = Query(None),
    cgpa_min: Optional[float] = Query(None),
    skills: Optional[str] = Query(None),
    skills_mode: str = Query("and"),
    exp_min: Optional[float] = Query(None),
    exp_max: Optional[float] = Query(None),
    location: Optional[str] = Query(None),
    grad_year: Optional[int] = Query(None),
    stage: Optional[str] = Query(None),
    jd_id: Optional[int] = Query(None),
    min_match: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query("id_asc"),
    db: Session = Depends(get_db)
):
    # Reuse identical filtering logic to match currently visible candidates exactly
    query = db.query(Candidate)

    if stage:
        query = query.filter(Candidate.pipeline_stage == stage)
    if tenth_min is not None:
        query = query.filter(Candidate.tenth_pct.isnot(None), Candidate.tenth_pct >= tenth_min)
    if twelfth_min is not None:
        query = query.filter(Candidate.twelfth_pct.isnot(None), Candidate.twelfth_pct >= twelfth_min)
    if cgpa_min is not None:
        query = query.filter(Candidate.cgpa_10.isnot(None), Candidate.cgpa_10 >= cgpa_min)
    if exp_min is not None:
        query = query.filter(Candidate.years_experience >= exp_min)
    if exp_max is not None:
        query = query.filter(Candidate.years_experience <= exp_max)
    if grad_year is not None:
        query = query.filter(Candidate.grad_year == grad_year)
    if location:
        query = query.filter(Candidate.location.ilike(f"%{location}%"))

    if search:
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Candidate.name.ilike(search_filter),
                Candidate.email.ilike(search_filter),
                Candidate.phone.ilike(search_filter),
                Candidate.college.ilike(search_filter),
                Candidate.degree.ilike(search_filter),
                Candidate.location.ilike(search_filter),
                Candidate.resume_text.ilike(search_filter)
            )
        )

    all_matched = query.all()

    # Skill filtering
    if skills:
        raw_list = [s.strip() for s in skills.split(",") if s.strip()]
        filter_skill_list = [normalize_skill(s) for s in raw_list if normalize_skill(s)]
        if filter_skill_list:
            filtered_by_skills = []
            is_and = (skills_mode.lower() == "and")
            for cand in all_matched:
                cand_skills = extract_skills_from_text(cand.resume_text or "")
                expanded = set(expand_skills_with_implications(cand_skills))
                if is_and:
                    if all(s in expanded for s in filter_skill_list):
                        filtered_by_skills.append(cand)
                else:
                    if any(s in expanded for s in filter_skill_list):
                        filtered_by_skills.append(cand)
            all_matched = filtered_by_skills

    # JD matching
    jd = None
    if jd_id:
        jd = db.query(JobDescription).filter(JobDescription.id == jd_id).first()

    candidates_export_data = []
    for cand in all_matched:
        extracted = extract_skills_from_text(cand.resume_text or "")
        match_score = None
        matched_s = []
        missing_s = []
        if jd:
            m_res = compute_candidate_match(cand, jd)
            match_score = m_res["match_score"]
            matched_s = m_res["breakdown"]["matched_skills"]
            missing_s = m_res["breakdown"]["missing_skills"]

        # Filter by min_match
        if min_match is not None and jd:
            if match_score is None or match_score < min_match:
                continue

        is_verified = not any(not ev.human_verified and ev.confidence in ["low", "medium"] for ev in (cand.evidence_fields or []))

        candidates_export_data.append({
            "name": cand.name,
            "email": cand.email,
            "phone": cand.phone,
            "location": cand.location,
            "degree": cand.degree,
            "college": cand.college,
            "tenth_pct": cand.tenth_pct,
            "twelfth_pct": cand.twelfth_pct,
            "cgpa_10": cand.cgpa_10,
            "years_experience": cand.years_experience,
            "grad_year": cand.grad_year,
            "skills": extracted,
            "match_score": match_score,
            "matched_skills": matched_s,
            "missing_skills": missing_s,
            "pipeline_stage": cand.pipeline_stage,
            "confidence": "verified" if is_verified else "needs review"
        })

    csv_content = generate_candidates_csv(candidates_export_data)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=hireswift_candidates.csv"}
    )

# Filter Presets Endpoints
@router.get("/presets", response_model=List[FilterPresetResponse])
def get_filter_presets(db: Session = Depends(get_db)):
    return db.query(FilterPreset).order_by(desc(FilterPreset.updated_at)).all()

@router.get("/presets/{preset_id}", response_model=FilterPresetResponse)
def get_filter_preset(preset_id: int, db: Session = Depends(get_db)):
    preset = db.query(FilterPreset).filter(FilterPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return preset

@router.post("/presets", response_model=FilterPresetResponse)
def create_filter_preset(payload: FilterPresetCreate, db: Session = Depends(get_db)):
    name_clean = payload.name.strip()
    if not name_clean:
        raise HTTPException(status_code=400, detail="Preset name cannot be empty")
    
    # Check duplicate
    existing = db.query(FilterPreset).filter(FilterPreset.name == name_clean).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Preset with name '{name_clean}' already exists")

    # Validate JSON
    try:
        json.loads(payload.filters_json)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid filters_json payload")

    preset = FilterPreset(name=name_clean, filters_json=payload.filters_json)
    db.add(preset)
    db.commit()
    db.refresh(preset)
    return preset

@router.put("/presets/{preset_id}", response_model=FilterPresetResponse)
def update_filter_preset(preset_id: int, payload: FilterPresetUpdate, db: Session = Depends(get_db)):
    preset = db.query(FilterPreset).filter(FilterPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    if payload.name is not None:
        name_clean = payload.name.strip()
        if not name_clean:
            raise HTTPException(status_code=400, detail="Preset name cannot be empty")
        existing = db.query(FilterPreset).filter(FilterPreset.name == name_clean, FilterPreset.id != preset_id).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Preset with name '{name_clean}' already exists")
        preset.name = name_clean

    if payload.filters_json is not None:
        try:
            json.loads(payload.filters_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid filters_json payload")
        preset.filters_json = payload.filters_json

    preset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(preset)
    return preset

@router.delete("/presets/{preset_id}")
def delete_filter_preset(preset_id: int, db: Session = Depends(get_db)):
    preset = db.query(FilterPreset).filter(FilterPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    db.delete(preset)
    db.commit()
    return {"status": "ok", "message": f"Preset '{preset.name}' deleted"}

@router.post("/whatif", response_model=WhatIfResponse)
def post_whatif_funnel(payload: WhatIfRequest, db: Session = Depends(get_db)):
    return evaluate_whatif_funnel(payload, db)

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    total_candidates = db.query(Candidate).count()
    applied = db.query(Candidate).filter(Candidate.pipeline_stage == "Applied").count()
    shortlisted = db.query(Candidate).filter(Candidate.pipeline_stage == "Shortlisted").count()
    interview = db.query(Candidate).filter(Candidate.pipeline_stage == "Interview").count()
    offers = db.query(Candidate).filter(Candidate.pipeline_stage == "Offer").count()
    rejected = db.query(Candidate).filter(Candidate.pipeline_stage == "Rejected").count()
    total_jds = db.query(JobDescription).count()

    # Confidence issues & review counts
    low_or_med_unverified = db.query(CandidateFieldEvidence).filter(
        CandidateFieldEvidence.human_verified == False,
        CandidateFieldEvidence.confidence.in_(["low", "medium"])
    ).all()
    fields_needing_verification = len(low_or_med_unverified)
    candidate_ids_with_issues = set(ev.candidate_id for ev in low_or_med_unverified)

    # Missing academic values also require review
    missing_academic_candidates = db.query(Candidate.id).filter(
        or_(
            Candidate.tenth_pct.is_(None),
            Candidate.twelfth_pct.is_(None),
            Candidate.cgpa_10.is_(None),
            Candidate.grad_year.is_(None)
        )
    ).all()
    for row in missing_academic_candidates:
        candidate_ids_with_issues.add(row[0])

    # Compute average JD match score against default primary JD if exists
    avg_match = 0.0
    primary_jd = db.query(JobDescription).first()
    if primary_jd and total_candidates > 0:
        cands_sample = db.query(Candidate).limit(50).all()
        scores = [compute_candidate_match(c, primary_jd)["match_score"] for c in cands_sample]
        if scores:
            avg_match = round(sum(scores) / len(scores), 1)

    return StatsResponse(
        total_candidates=total_candidates,
        applied=applied,
        shortlisted=shortlisted,
        interview=interview,
        offers=offers,
        rejected=rejected,
        total_jds=total_jds,
        average_jd_match=avg_match,
        candidates_with_confidence_issues=len(candidate_ids_with_issues),
        candidates_requiring_review=len(candidate_ids_with_issues),
        fields_needing_verification=fields_needing_verification
    )

@router.get("/candidates/review-queue", response_model=List[CandidateResponse])
def get_review_queue(db: Session = Depends(get_db)):
    """
    Returns candidates requiring human recruiter review:
    - low/medium unverified parsing confidence
    - missing academic fields
    """
    # 1. Unverified low/medium confidence fields
    unverified_ev = db.query(CandidateFieldEvidence).filter(
        CandidateFieldEvidence.human_verified == False,
        CandidateFieldEvidence.confidence.in_(["low", "medium"])
    ).all()
    review_ids = set(ev.candidate_id for ev in unverified_ev)

    # 2. Missing core fields
    missing_cands = db.query(Candidate).filter(
        or_(
            Candidate.tenth_pct.is_(None),
            Candidate.twelfth_pct.is_(None),
            Candidate.cgpa_10.is_(None),
            Candidate.grad_year.is_(None)
        )
    ).all()
    for c in missing_cands:
        review_ids.add(c.id)

    candidates = db.query(Candidate).filter(Candidate.id.in_(review_ids)).all()
    results = []
    for cand in candidates:
        resp = CandidateResponse.model_validate(cand)
        resp.needs_review = True
        resp.skills = extract_skills_from_text(cand.resume_text or "")
        results.append(resp)
    return results

@router.get("/candidates", response_model=PaginatedCandidateResponse)
def get_candidates(
    tenth_min: Optional[float] = Query(None),
    twelfth_min: Optional[float] = Query(None),
    cgpa_min: Optional[float] = Query(None),
    skills: Optional[str] = Query(None),
    skills_mode: str = Query("and"),
    exp_min: Optional[float] = Query(None),
    exp_max: Optional[float] = Query(None),
    location: Optional[str] = Query(None),
    grad_year: Optional[int] = Query(None),
    stage: Optional[str] = Query(None),
    jd_id: Optional[int] = Query(None),
    min_match: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query("id_asc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Candidate)

    # 1. SQL-level filters
    if stage:
        query = query.filter(Candidate.pipeline_stage == stage)
    if tenth_min is not None:
        query = query.filter(Candidate.tenth_pct.isnot(None), Candidate.tenth_pct >= tenth_min)
    if twelfth_min is not None:
        query = query.filter(Candidate.twelfth_pct.isnot(None), Candidate.twelfth_pct >= twelfth_min)
    if cgpa_min is not None:
        query = query.filter(Candidate.cgpa_10.isnot(None), Candidate.cgpa_10 >= cgpa_min)
    if exp_min is not None:
        query = query.filter(Candidate.years_experience >= exp_min)
    if exp_max is not None:
        query = query.filter(Candidate.years_experience <= exp_max)
    if grad_year is not None:
        query = query.filter(Candidate.grad_year == grad_year)
    if location:
        query = query.filter(Candidate.location.ilike(f"%{location}%"))

    # Comprehensive multi-field text search
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Candidate.name.ilike(search_filter),
                Candidate.email.ilike(search_filter),
                Candidate.phone.ilike(search_filter),
                Candidate.college.ilike(search_filter),
                Candidate.degree.ilike(search_filter),
                Candidate.location.ilike(search_filter),
                Candidate.resume_text.ilike(search_filter)
            )
        )

    all_matched = query.all()

    # 2. Skill filtering with shared normalize_skill()
    filter_skill_list = []
    if skills:
        raw_list = [s.strip() for s in skills.split(",") if s.strip()]
        filter_skill_list = [normalize_skill(s) for s in raw_list if normalize_skill(s)]

    if filter_skill_list:
        filtered_by_skills = []
        is_and = (skills_mode.lower() == "and")

        for cand in all_matched:
            cand_skills = extract_skills_from_text(cand.resume_text or "")
            expanded = set(expand_skills_with_implications(cand_skills))

            if is_and:
                if all(s in expanded for s in filter_skill_list):
                    filtered_by_skills.append(cand)
            else:
                if any(s in expanded for s in filter_skill_list):
                    filtered_by_skills.append(cand)
        all_matched = filtered_by_skills

    # 3. JD Matching computation if jd_id provided
    jd = None
    if jd_id:
        jd = db.query(JobDescription).filter(JobDescription.id == jd_id).first()

    annotated_candidates = []
    for cand in all_matched:
        resp = CandidateResponse.model_validate(cand)
        resp.skills = extract_skills_from_text(cand.resume_text or "")
        
        # Check if candidate needs review
        has_unverified = any(not ev.human_verified and ev.confidence in ["low", "medium"] for ev in cand.evidence_fields)
        missing_core = any(v is None for v in [cand.tenth_pct, cand.twelfth_pct, cand.cgpa_10, cand.grad_year])
        resp.needs_review = has_unverified or missing_core

        if jd:
            match_res = compute_candidate_match(cand, jd)
            resp.match_score = match_res["match_score"]
            resp.match_breakdown = match_res["breakdown"]
        annotated_candidates.append(resp)

    # Filter by min_match if specified
    if min_match is not None and jd:
        annotated_candidates = [c for c in annotated_candidates if c.match_score is not None and c.match_score >= min_match]

    # 4. Sorting
    if sort == "match_desc":
        annotated_candidates.sort(key=lambda x: (x.match_score or 0.0), reverse=True)
    elif sort == "cgpa_desc":
        annotated_candidates.sort(key=lambda x: (x.cgpa_10 or 0.0), reverse=True)
    elif sort == "exp_desc":
        annotated_candidates.sort(key=lambda x: (x.years_experience or 0.0), reverse=True)
    elif sort == "id_desc":
        annotated_candidates.sort(key=lambda x: x.id, reverse=True)
    else:
        annotated_candidates.sort(key=lambda x: x.id)

    # 5. Pagination
    total = len(annotated_candidates)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_items = annotated_candidates[start_idx:end_idx]

    return PaginatedCandidateResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=paginated_items
    )

# Phase 7: Bulk Email SMTP Dry-Run & Templates
@router.get("/email/templates")
def get_email_templates():
    return EMAIL_TEMPLATES

@router.post("/email/bulk", response_model=BulkEmailResponse)
def bulk_email_endpoint(payload: BulkEmailRequest):
    result = process_bulk_email_queue(
        items=[item.model_dump() for item in payload.candidates],
        template_key=payload.template_key,
        role=payload.role,
        dry_run=payload.dry_run,
        smtp_host=payload.smtp_host,
        smtp_port=payload.smtp_port,
        smtp_user=payload.smtp_user,
        smtp_password=payload.smtp_password
    )
    return result

# Phase 7: Duplicate Resume Detection & Review
@router.get("/candidates/{candidate_id}/duplicates", response_model=DuplicateCheckResponse)
def check_candidate_duplicates(candidate_id: int, threshold: float = Query(70.0), db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    matches = find_duplicates_for_candidate(candidate, db, threshold=threshold)
    return {
        "candidate_id": candidate_id,
        "has_duplicates": len(matches) > 0,
        "duplicate_count": len(matches),
        "matches": matches
    }

@router.post("/candidates/{candidate_id}/mark-duplicate")
def mark_candidate_as_duplicate(candidate_id: int, payload: DuplicateMarkRequest, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    target = db.query(Candidate).filter(Candidate.id == payload.duplicate_of_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target duplicate candidate not found")
    
    candidate.is_duplicate = True
    candidate.duplicate_of_id = target.id
    candidate.pipeline_stage = "Rejected"
    
    # Audit log
    db.add(AuditLog(
        candidate_id=candidate.id,
        from_stage=candidate.pipeline_stage,
        to_stage="Rejected",
        changed_by=f"recruiter (Marked as duplicate of Candidate #{target.id}: {target.name})",
        changed_at=datetime.utcnow()
    ))
    db.commit()
    return {"status": "ok", "message": f"Candidate #{candidate.id} marked as duplicate of #{target.id}"}

# Phase 7: Skill-Gap Insights
@router.get("/candidates/{candidate_id}/skill-gap", response_model=SkillGapResponse)
def get_candidate_skill_gap(candidate_id: int, jd_id: int = Query(...), db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    jd = db.query(JobDescription).filter(JobDescription.id == jd_id).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    
    return analyze_skill_gap(candidate, jd)

# Phase 7: Evidence-Based Hiring Intelligence, Evidence Score, Interview Probes & Graph
@router.get("/candidates/{candidate_id}/intelligence", response_model=HiringIntelligenceResponse)
def get_candidate_hiring_intelligence(candidate_id: int, jd_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    jd = None
    if jd_id:
        jd = db.query(JobDescription).filter(JobDescription.id == jd_id).first()
    
    return analyze_hiring_intelligence(candidate, jd)

@router.get("/candidates/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: int, jd_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    resp = CandidateResponse.model_validate(candidate)
    resp.skills = extract_skills_from_text(candidate.resume_text or "")
    
    has_unverified = any(not ev.human_verified and ev.confidence in ["low", "medium"] for ev in candidate.evidence_fields)
    missing_core = any(v is None for v in [candidate.tenth_pct, candidate.twelfth_pct, candidate.cgpa_10, candidate.grad_year])
    resp.needs_review = has_unverified or missing_core

    if jd_id:
        jd = db.query(JobDescription).filter(JobDescription.id == jd_id).first()
        if jd:
            match_res = compute_candidate_match(candidate, jd)
            resp.match_score = match_res["match_score"]
            resp.match_breakdown = match_res["breakdown"]
    return resp

@router.patch("/candidates/{candidate_id}", response_model=CandidateResponse)
def update_candidate(candidate_id: int, payload: CandidateUpdate, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    audit_changes = []

    # Update candidate fields and log changes
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        if field_name == "skills":
            continue
        old_val = getattr(candidate, field_name, None)
        if old_val != value:
            setattr(candidate, field_name, value)
            audit_changes.append(f"{field_name}: {old_val} -> {value}")

    # If skills were passed, append or update in resume_text
    if payload.skills is not None:
        normalized_list = [normalize_skill(s) for s in payload.skills if normalize_skill(s)]
        skills_str = ", ".join(normalized_list)
        candidate.resume_text = (candidate.resume_text or "") + f"\nUpdated Skills: {skills_str}"
        audit_changes.append(f"skills updated to: {skills_str}")

    candidate.updated_at = datetime.utcnow()

    # Record audit log
    if audit_changes:
        db.add(AuditLog(
            candidate_id=candidate.id,
            from_stage=candidate.pipeline_stage,
            to_stage=candidate.pipeline_stage,
            changed_by="recruiter",
            changed_at=datetime.utcnow()
        ))

    db.commit()
    db.refresh(candidate)

    resp = CandidateResponse.model_validate(candidate)
    resp.skills = extract_skills_from_text(candidate.resume_text or "")
    return resp

@router.patch("/candidates/{candidate_id}/stage", response_model=CandidateResponse)
def update_candidate_stage(candidate_id: int, payload: CandidateStageUpdate, db: Session = Depends(get_db)):
    if payload.stage not in VALID_STAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stage '{payload.stage}'. Allowed stages: {', '.join(sorted(VALID_STAGES))}"
        )

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    old_stage = candidate.pipeline_stage
    candidate.pipeline_stage = payload.stage
    candidate.updated_at = datetime.utcnow()

    # Record AuditLog
    db.add(AuditLog(
        candidate_id=candidate.id,
        from_stage=old_stage,
        to_stage=payload.stage,
        changed_by="recruiter",
        changed_at=datetime.utcnow()
    ))

    db.commit()
    db.refresh(candidate)

    resp = CandidateResponse.model_validate(candidate)
    resp.skills = extract_skills_from_text(candidate.resume_text or "")
    return resp

@router.post("/candidates/{candidate_id}/verify-evidence", response_model=CandidateResponse)
def verify_candidate_evidence(candidate_id: int, payload: VerifyEvidenceRequest, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    ev = db.query(CandidateFieldEvidence).filter(
        CandidateFieldEvidence.candidate_id == candidate_id,
        CandidateFieldEvidence.field_name == payload.field_name
    ).first()

    old_val = ev.value if ev else None
    new_val = payload.value if payload.value is not None else old_val

    if not ev:
        # Create evidence if not yet existing
        ev = CandidateFieldEvidence(
            candidate_id=candidate_id,
            field_name=payload.field_name,
            value=new_val,
            confidence="verified",
            source_text=f"Recruiter verified: {new_val}",
            human_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(ev)
    else:
        ev.value = new_val
        ev.confidence = "verified"
        ev.human_verified = True
        ev.updated_at = datetime.utcnow()

    # Also update the primary candidate model field if applicable
    if hasattr(candidate, payload.field_name):
        try:
            if payload.field_name in ["tenth_pct", "twelfth_pct", "cgpa_10", "years_experience"]:
                setattr(candidate, payload.field_name, float(new_val) if new_val is not None else None)
            elif payload.field_name == "grad_year":
                setattr(candidate, payload.field_name, int(new_val) if new_val is not None else None)
            else:
                setattr(candidate, payload.field_name, new_val)
        except Exception:
            pass

    # Record audit entry
    db.add(AuditLog(
        candidate_id=candidate.id,
        from_stage=candidate.pipeline_stage,
        to_stage=candidate.pipeline_stage,
        changed_by=f"recruiter (Verified {payload.field_name}: {old_val} -> {new_val})",
        changed_at=datetime.utcnow()
    ))

    db.commit()
    db.refresh(candidate)

    resp = CandidateResponse.model_validate(candidate)
    resp.skills = extract_skills_from_text(candidate.resume_text or "")
    return resp

@router.get("/candidates/{candidate_id}/audit", response_model=List[AuditLogResponse])
def get_candidate_audit_history(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    logs = db.query(AuditLog).filter(
        AuditLog.candidate_id == candidate_id
    ).order_by(desc(AuditLog.changed_at)).all()
    
    return logs

@router.get("/jds", response_model=List[JobDescriptionResponse])
def get_jds(db: Session = Depends(get_db)):
    return db.query(JobDescription).all()

@router.post("/jds", response_model=JobDescriptionResponse)
def create_jd_from_text(payload: JobDescriptionCreate, db: Session = Depends(get_db)):
    parsed = parse_job_description_text(payload.raw_text, title=payload.title or "New Position")
    
    new_jd = JobDescription(
        title=parsed["title"],
        description=parsed["description"],
        min_experience=parsed["min_experience"],
        required_skills=", ".join(parsed["required_skills"]),
        nice_to_have_skills=", ".join(parsed["nice_to_have_skills"])
    )
    db.add(new_jd)
    db.commit()
    db.refresh(new_jd)
    return new_jd


@router.post("/resumes/upload", response_model=CandidateResponse)
async def upload_and_parse_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    filename = file.filename or "uploaded_resume.pdf"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed formats: .pdf, .docx, .txt"
        )

    # Save to tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp_path = tmp.name
        content = await file.read()
        tmp.write(content)

    try:
        parsed = parse_resume(tmp_path)
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=422, detail=f"Failed to parse resume: {str(e)}")

    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    # Check for duplicate by email or resume_filename
    cand = None
    if parsed.get("email"):
        cand = db.query(Candidate).filter(Candidate.email == parsed["email"]).first()
    if not cand:
        cand = db.query(Candidate).filter(Candidate.resume_filename == filename).first()

    if not cand:
        cand = Candidate(
            name=parsed.get("name") or os.path.splitext(filename)[0].replace("_", " ").title(),
            email=parsed.get("email"),
            phone=parsed.get("phone"),
            location=parsed.get("location"),
            college=parsed.get("college"),
            degree=parsed.get("degree"),
            grad_year=parsed.get("grad_year"),
            tenth_pct=parsed.get("tenth_pct"),
            twelfth_pct=parsed.get("twelfth_pct"),
            cgpa_10=parsed.get("cgpa_10"),
            years_experience=float(parsed.get("years_experience") or 0.0),
            resume_filename=filename,
            resume_text=parsed.get("resume_text", ""),
            pipeline_stage="Applied"
        )
        db.add(cand)
        db.flush()

        # Audit log creation
        db.add(AuditLog(
            candidate_id=cand.id,
            from_stage=None,
            to_stage="Applied",
            changed_by="Resume Upload Pipeline"
        ))
    else:
        # Update existing record
        cand.name = parsed.get("name") or cand.name
        cand.email = parsed.get("email") or cand.email
        cand.phone = parsed.get("phone") or cand.phone
        cand.location = parsed.get("location") or cand.location
        cand.college = parsed.get("college") or cand.college
        cand.degree = parsed.get("degree") or cand.degree
        cand.grad_year = parsed.get("grad_year") or cand.grad_year
        cand.tenth_pct = parsed.get("tenth_pct") if parsed.get("tenth_pct") is not None else cand.tenth_pct
        cand.twelfth_pct = parsed.get("twelfth_pct") if parsed.get("twelfth_pct") is not None else cand.twelfth_pct
        cand.cgpa_10 = parsed.get("cgpa_10") if parsed.get("cgpa_10") is not None else cand.cgpa_10
        cand.years_experience = float(parsed.get("years_experience") or cand.years_experience)
        cand.resume_text = parsed.get("resume_text") or cand.resume_text

    # Store / update extracted evidence
    db.query(CandidateFieldEvidence).filter(CandidateFieldEvidence.candidate_id == cand.id).delete()
    for ev in parsed.get("evidence", []):
        db.add(CandidateFieldEvidence(
            candidate_id=cand.id,
            field_name=ev["field_name"],
            value=ev.get("value"),
            confidence=ev.get("confidence", "medium"),
            source_text=ev.get("source_text"),
            human_verified=ev.get("human_verified", False)
        ))

    db.commit()
    db.refresh(cand)
    return cand
