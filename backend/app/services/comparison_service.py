import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import Candidate, JobDescription
from app.schemas.comparison import (
    CandidateComparisonCard,
    CandidateCompareResponse
)
from app.services.matching_service import compute_candidate_match
from app.services.skills_service import (
    extract_skills_from_text,
    expand_skills_with_implications,
    normalize_skill
)

def compare_candidates_service(candidate_ids: List[int], jd_id: Optional[int], db: Session) -> CandidateCompareResponse:
    if len(candidate_ids) < 2 or len(candidate_ids) > 3:
        raise ValueError("Comparison requires exactly 2 or 3 candidates.")

    candidates: List[Candidate] = db.query(Candidate).filter(Candidate.id.in_(candidate_ids)).all()
    if len(candidates) != len(candidate_ids):
        raise ValueError("One or more candidates could not be found.")

    # Maintain requested order
    candidates_dict = {c.id: c for c in candidates}
    ordered_cands = [candidates_dict[cid] for cid in candidate_ids]

    jd: Optional[JobDescription] = None
    if jd_id:
        jd = db.query(JobDescription).filter(JobDescription.id == jd_id).first()

    # Prepare skills and matching details for each candidate
    candidate_cards: List[CandidateComparisonCard] = []
    cand_skill_sets: Dict[int, set] = {}

    for c in ordered_cands:
        extracted = extract_skills_from_text(c.resume_text or "")
        cand_skill_sets[c.id] = set(extracted)

    # Compute shared skills across all candidates
    shared_skills = sorted(list(set.intersection(*cand_skill_sets.values()))) if cand_skill_sets else []

    for c in ordered_cands:
        my_skills = cand_skill_sets[c.id]
        # Unique skills (not present in any other candidate in this comparison)
        other_skills = set.union(*(cand_skill_sets[oid] for oid in cand_skill_sets if oid != c.id)) if len(cand_skill_sets) > 1 else set()
        unique_skills = sorted(list(my_skills - other_skills))

        # Check evidence issues
        issues = []
        is_verified = True
        for ev in (c.evidence_fields or []):
            if not ev.human_verified and ev.confidence in ["low", "medium"]:
                issues.append(f"{ev.field_name} ({ev.confidence})")
                is_verified = False
        if c.cgpa_10 is None:
            issues.append("Missing CGPA")
            is_verified = False
        if c.tenth_pct is None:
            issues.append("Missing 10th %")
            is_verified = False
        if c.twelfth_pct is None:
            issues.append("Missing 12th %")
            is_verified = False

        # JD matching breakdown
        match_score = None
        matched_skills = []
        missing_skills = []
        exp_score = 0.0
        edu_score = 0.0
        skills_score = 0.0

        if jd:
            match_res = compute_candidate_match(c, jd)
            match_score = match_res["match_score"]
            matched_skills = match_res["breakdown"]["matched_skills"]
            missing_skills = match_res["breakdown"]["missing_skills"]
            skills_score = (match_res["breakdown"]["skills_score"] / 50.0) * 100.0
            exp_score = (match_res["breakdown"]["experience_score"] / 25.0) * 100.0
            edu_score = (match_res["breakdown"]["education_score"] / 15.0) * 100.0
        else:
            # Fallback normalized scoring if no JD selected
            skills_score = min(100.0, len(my_skills) * 15.0)
            exp_score = min(100.0, (c.years_experience or 0.0) * 25.0)
            edu_score = min(100.0, ((c.cgpa_10 or 7.0) / 10.0) * 100.0)
            match_score = round((skills_score * 0.4 + exp_score * 0.3 + edu_score * 0.3), 1)

        norm_dimensions = {
            "Skills": round(skills_score, 1),
            "Experience": round(exp_score, 1),
            "Education": round(edu_score, 1),
            "JD Match": round(float(match_score), 1)
        }

        card = CandidateComparisonCard(
            candidate_id=c.id,
            name=c.name,
            location=c.location,
            degree=c.degree,
            college=c.college,
            tenth_pct=c.tenth_pct,
            twelfth_pct=c.twelfth_pct,
            cgpa_10=c.cgpa_10,
            years_experience=c.years_experience or 0.0,
            grad_year=c.grad_year,
            skills=sorted(list(my_skills)),
            pipeline_stage=c.pipeline_stage,
            jd_match_score=match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            unique_skills=unique_skills,
            shared_skills=shared_skills,
            confidence_issues=issues,
            is_verified=is_verified,
            normalized_scores=norm_dimensions
        )
        candidate_cards.append(card)

    # Format radar chart data for Recharts
    # [{"dimension": "Skills", "Akash (ID: 1)": 85, "Rahul (ID: 2)": 75}, ...]
    # Use unique label (e.g. "Name (ID: #)" or unique key) to prevent key collision when candidates share names
    radar_data = []
    for dim in ["Skills", "Experience", "Education", "JD Match"]:
        dim_entry: Dict[str, Any] = {"dimension": dim}
        for card in candidate_cards:
            key_label = f"{card.name} (#{card.candidate_id})"
            dim_entry[key_label] = card.normalized_scores.get(dim, 0.0)
        radar_data.append(dim_entry)

    # Deterministic Verdict Generation
    # Compare match scores, experience, skills
    sorted_by_match = sorted(candidate_cards, key=lambda x: (x.jd_match_score or 0.0), reverse=True)
    best_cand = sorted_by_match[0]
    second_cand = sorted_by_match[1]

    score_diff = (best_cand.jd_match_score or 0.0) - (second_cand.jd_match_score or 0.0)

    relative_strengths = {}
    for card in candidate_cards:
        strengths = []
        if (card.cgpa_10 or 0) >= 8.5:
            strengths.append("High CGPA")
        if card.years_experience >= 2.0:
            strengths.append("Strong Experience")
        if (card.jd_match_score or 0) >= 80.0:
            strengths.append("Strong JD Alignment")
        if len(card.skills) >= 6:
            strengths.append("Broad Skillset")
        relative_strengths[card.name] = ", ".join(strengths) if strengths else "Balanced Profile"

    if score_diff < 3.0:
        # Closely matched scenario
        verdict = f"{best_cand.name} and {second_cand.name} are closely matched. {best_cand.name} leads in JD alignment ({best_cand.jd_match_score}%), while {second_cand.name} ({second_cand.jd_match_score}%) offers competitive {relative_strengths.get(second_cand.name, 'skills')}."
    else:
        # Clear leader scenario
        reasons = []
        if (best_cand.jd_match_score or 0) > (second_cand.jd_match_score or 0):
            reasons.append(f"higher JD alignment ({best_cand.jd_match_score}% vs {second_cand.jd_match_score}%)")
        if best_cand.years_experience > second_cand.years_experience:
            reasons.append(f"more professional experience ({best_cand.years_experience} yrs vs {second_cand.years_experience} yrs)")
        if len(best_cand.skills) > len(second_cand.skills):
            reasons.append("broader verified skill coverage")
        
        reason_str = ", ".join(reasons) if reasons else "higher overall score composite"
        verdict = f"{best_cand.name} is the strongest overall candidate, driven by {reason_str}."

    return CandidateCompareResponse(
        candidates=candidate_cards,
        radar_data=radar_data,
        verdict=verdict,
        shared_skills=shared_skills,
        relative_strengths=relative_strengths
    )
