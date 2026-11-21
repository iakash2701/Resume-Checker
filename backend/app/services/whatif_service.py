from typing import Dict, Any, List, Set, Optional
from sqlalchemy.orm import Session
from app.models import Candidate, JobDescription
from app.schemas.whatif import (
    WhatIfRequest,
    WhatIfResponse,
    FunnelStage,
    NearMissCandidate,
    HighMatchRemovedCandidate,
    RelaxationSuggestion
)
from app.services.matching_service import compute_candidate_match
from app.services.skills_service import (
    normalize_skill,
    extract_skills_from_text,
    expand_skills_with_implications
)

def evaluate_whatif_funnel(request: WhatIfRequest, db: Session) -> WhatIfResponse:
    # 1. Fetch candidates and optional JD
    candidates: List[Candidate] = db.query(Candidate).all()
    total_count = len(candidates)

    jd: Optional[JobDescription] = None
    if request.jd_id:
        jd = db.query(JobDescription).filter(JobDescription.id == request.jd_id).first()

    # Pre-compute JD match scores for all candidates if jd is selected
    match_scores: Dict[int, Dict[str, Any]] = {}
    if jd:
        for cand in candidates:
            match_scores[cand.id] = compute_candidate_match(cand, jd)

    # Pre-extract expanded skills for all candidates
    candidate_skills: Dict[int, Set[str]] = {}
    for cand in candidates:
        extracted = extract_skills_from_text(cand.resume_text or "")
        expanded = set(expand_skills_with_implications(extracted))
        candidate_skills[cand.id] = expanded

    # 2. Sequential Filter Pipeline Definition
    filter_definitions = []

    if request.tenth_pct is not None:
        filter_definitions.append({
            "name": f"10th ≥ {request.tenth_pct}%",
            "field": "tenth_pct",
            "threshold": request.tenth_pct,
            "check": lambda c: c.tenth_pct is not None and c.tenth_pct >= request.tenth_pct,
            "gap_calc": lambda c: (request.tenth_pct - c.tenth_pct) if c.tenth_pct is not None else None,
            "actual_val": lambda c: c.tenth_pct
        })

    if request.twelfth_pct is not None:
        filter_definitions.append({
            "name": f"12th ≥ {request.twelfth_pct}%",
            "field": "twelfth_pct",
            "threshold": request.twelfth_pct,
            "check": lambda c: c.twelfth_pct is not None and c.twelfth_pct >= request.twelfth_pct,
            "gap_calc": lambda c: (request.twelfth_pct - c.twelfth_pct) if c.twelfth_pct is not None else None,
            "actual_val": lambda c: c.twelfth_pct
        })

    if request.cgpa is not None:
        filter_definitions.append({
            "name": f"CGPA ≥ {request.cgpa}",
            "field": "cgpa",
            "threshold": request.cgpa,
            "check": lambda c: c.cgpa_10 is not None and c.cgpa_10 >= request.cgpa,
            "gap_calc": lambda c: (request.cgpa - c.cgpa_10) if c.cgpa_10 is not None else None,
            "actual_val": lambda c: c.cgpa_10
        })

    if request.skills:
        norm_req_skills = [normalize_skill(s) for s in request.skills if normalize_skill(s)]
        if norm_req_skills:
            mode_upper = request.skill_mode.upper()
            skill_label = f"Skills ({mode_upper}): {', '.join(norm_req_skills)}"

            if mode_upper == "AND":
                def skill_check(c):
                    cand_s = candidate_skills.get(c.id, set())
                    return all(s in cand_s for s in norm_req_skills)
            else:
                def skill_check(c):
                    cand_s = candidate_skills.get(c.id, set())
                    return any(s in cand_s for s in norm_req_skills)

            filter_definitions.append({
                "name": skill_label,
                "field": "skills",
                "threshold": norm_req_skills,
                "check": skill_check,
                "gap_calc": lambda c: None,
                "actual_val": lambda c: list(candidate_skills.get(c.id, set()))
            })

    if request.years_experience is not None:
        filter_definitions.append({
            "name": f"Experience ≥ {request.years_experience} yr",
            "field": "years_experience",
            "threshold": request.years_experience,
            "check": lambda c: (c.years_experience or 0.0) >= request.years_experience,
            "gap_calc": lambda c: (request.years_experience - (c.years_experience or 0.0)),
            "actual_val": lambda c: (c.years_experience or 0.0)
        })

    if request.location:
        loc_clean = request.location.strip().lower()
        filter_definitions.append({
            "name": f"Location: {request.location}",
            "field": "location",
            "threshold": request.location,
            "check": lambda c: loc_clean in (c.location or "").lower(),
            "gap_calc": lambda c: None,
            "actual_val": lambda c: c.location
        })

    if request.grad_year is not None:
        filter_definitions.append({
            "name": f"Grad Year: {request.grad_year}",
            "field": "grad_year",
            "threshold": request.grad_year,
            "check": lambda c: c.grad_year == request.grad_year,
            "gap_calc": lambda c: None,
            "actual_val": lambda c: c.grad_year
        })

    if request.min_match_score is not None and jd:
        filter_definitions.append({
            "name": f"JD Match ≥ {request.min_match_score}",
            "field": "min_match_score",
            "threshold": request.min_match_score,
            "check": lambda c: match_scores.get(c.id, {}).get("match_score", 0.0) >= request.min_match_score,
            "gap_calc": lambda c: (request.min_match_score - match_scores.get(c.id, {}).get("match_score", 0.0)),
            "actual_val": lambda c: match_scores.get(c.id, {}).get("match_score", 0.0)
        })

    # 3. Sequential Execution of Funnel Stages
    funnel_stages: List[FunnelStage] = []
    current_pool = list(candidates)

    for fdef in filter_definitions:
        before_cnt = len(current_pool)
        current_pool = [c for c in current_pool if fdef["check"](c)]
        after_cnt = len(current_pool)
        removed_cnt = before_cnt - after_cnt
        pct_removed = round((removed_cnt / before_cnt * 100.0), 1) if before_cnt > 0 else 0.0

        funnel_stages.append(FunnelStage(
            filter=fdef["name"],
            before=before_cnt,
            after=after_cnt,
            removed=removed_cnt,
            percentage_removed=pct_removed
        ))

    passing_candidates = set(c.id for c in current_pool)
    removed_count = total_count - len(passing_candidates)

    # 4. Multi-Filter Failure Map per Candidate (for Near-Miss and High-Match Exclusions)
    # failure_map[cand_id] = list of failed filter definitions
    failure_map: Dict[int, List[Dict[str, Any]]] = {}
    for cand in candidates:
        failed = []
        for fdef in filter_definitions:
            if not fdef["check"](cand):
                failed.append(fdef)
        failure_map[cand.id] = failed

    # 5. Near-Miss Candidate Identification
    # Near-miss: Failed only 1 filter (or 2 at most), and the gap is small:
    #   CGPA: gap <= 0.5
    #   10th / 12th: gap <= 5.0%
    #   Experience: gap <= 0.6 yrs
    #   Match score: gap <= 6.0
    near_miss_candidates: List[NearMissCandidate] = []

    for cand in candidates:
        if cand.id in passing_candidates:
            continue
        failed_filters = failure_map[cand.id]
        if len(failed_filters) == 1:
            failed_f = failed_filters[0]
            field_name = failed_f["field"]
            gap = failed_f["gap_calc"](cand)
            act_val = failed_f["actual_val"](cand)

            is_near_miss = False
            if gap is not None and gap > 0:
                if field_name == "cgpa" and gap <= 0.5:
                    is_near_miss = True
                elif field_name in ["tenth_pct", "twelfth_pct"] and gap <= 5.0:
                    is_near_miss = True
                elif field_name == "years_experience" and gap <= 0.6:
                    is_near_miss = True
                elif field_name == "min_match_score" and gap <= 6.0:
                    is_near_miss = True

            if is_near_miss:
                m_score = match_scores.get(cand.id, {}).get("match_score") if jd else None
                near_miss_candidates.append(NearMissCandidate(
                    candidate_id=cand.id,
                    name=cand.name,
                    failed_filter=failed_f["name"],
                    actual=act_val,
                    required=failed_f["threshold"],
                    gap=round(gap, 2),
                    total_failures=1,
                    match_score=m_score
                ))

    # Sort near misses by smallest gap
    near_miss_candidates.sort(key=lambda x: x.gap)

    # 6. High-Match Removed Candidates
    # Criteria: JD selected, candidate match score >= 75 (or >= min_match_score - 5), but excluded by filters
    high_match_removed: List[HighMatchRemovedCandidate] = []
    if jd:
        high_threshold = max(75.0, (request.min_match_score - 10.0) if request.min_match_score else 75.0)
        for cand in candidates:
            if cand.id not in passing_candidates:
                cand_score = match_scores.get(cand.id, {}).get("match_score", 0.0)
                if cand_score >= high_threshold:
                    failed_names = [f["name"] for f in failure_map[cand.id]]
                    high_match_removed.append(HighMatchRemovedCandidate(
                        candidate_id=cand.id,
                        name=cand.name,
                        match_score=cand_score,
                        failed_filters=failed_names,
                        details={
                            "cgpa": cand.cgpa_10,
                            "experience": cand.years_experience,
                            "tenth": cand.tenth_pct,
                            "twelfth": cand.twelfth_pct
                        }
                    ))
        high_match_removed.sort(key=lambda x: x.match_score, reverse=True)

    # 7. Relaxation Suggestions (Useful, realistic threshold reductions)
    relaxation_suggestions: List[RelaxationSuggestion] = []

    # A. CGPA relaxation (e.g. relax by 0.5)
    if request.cgpa is not None and request.cgpa > 5.0:
        suggested_cgpa = round(request.cgpa - 0.5, 1)
        # Check how many candidates would pass ALL filters if CGPA were relaxed to suggested_cgpa
        recovered = 0
        for cand in candidates:
            if cand.id in passing_candidates:
                continue
            # Must pass all OTHER filters, and pass relaxed CGPA
            other_failed = [f for f in failure_map[cand.id] if f["field"] != "cgpa"]
            if not other_failed:
                if cand.cgpa_10 is not None and cand.cgpa_10 >= suggested_cgpa:
                    recovered += 1
        if recovered > 0:
            relaxation_suggestions.append(RelaxationSuggestion(
                filter_name="CGPA",
                current_value=request.cgpa,
                suggested_value=suggested_cgpa,
                description=f"Relax CGPA from {request.cgpa} → {suggested_cgpa}",
                recovered_count=recovered,
                field_key="cgpa"
            ))

    # B. 10th % relaxation (e.g. relax by 5%)
    if request.tenth_pct is not None and request.tenth_pct > 50.0:
        suggested_10th = round(request.tenth_pct - 5.0, 1)
        recovered = 0
        for cand in candidates:
            if cand.id in passing_candidates:
                continue
            other_failed = [f for f in failure_map[cand.id] if f["field"] != "tenth_pct"]
            if not other_failed:
                if cand.tenth_pct is not None and cand.tenth_pct >= suggested_10th:
                    recovered += 1
        if recovered > 0:
            relaxation_suggestions.append(RelaxationSuggestion(
                filter_name="10th Percentage",
                current_value=request.tenth_pct,
                suggested_value=suggested_10th,
                description=f"Relax 10th from {request.tenth_pct}% → {suggested_10th}%",
                recovered_count=recovered,
                field_key="tenth_pct"
            ))

    # C. 12th % relaxation (e.g. relax by 5%)
    if request.twelfth_pct is not None and request.twelfth_pct > 50.0:
        suggested_12th = round(request.twelfth_pct - 5.0, 1)
        recovered = 0
        for cand in candidates:
            if cand.id in passing_candidates:
                continue
            other_failed = [f for f in failure_map[cand.id] if f["field"] != "twelfth_pct"]
            if not other_failed:
                if cand.twelfth_pct is not None and cand.twelfth_pct >= suggested_12th:
                    recovered += 1
        if recovered > 0:
            relaxation_suggestions.append(RelaxationSuggestion(
                filter_name="12th Percentage",
                current_value=request.twelfth_pct,
                suggested_value=suggested_12th,
                description=f"Relax 12th from {request.twelfth_pct}% → {suggested_12th}%",
                recovered_count=recovered,
                field_key="twelfth_pct"
            ))

    # D. Experience relaxation (e.g. relax by 0.5 or 1 yr)
    if request.years_experience is not None and request.years_experience > 0.0:
        step = 0.5 if request.years_experience <= 2.0 else 1.0
        suggested_exp = max(0.0, round(request.years_experience - step, 1))
        recovered = 0
        for cand in candidates:
            if cand.id in passing_candidates:
                continue
            other_failed = [f for f in failure_map[cand.id] if f["field"] != "years_experience"]
            if not other_failed:
                if (cand.years_experience or 0.0) >= suggested_exp:
                    recovered += 1
        if recovered > 0:
            relaxation_suggestions.append(RelaxationSuggestion(
                filter_name="Experience",
                current_value=request.years_experience,
                suggested_value=suggested_exp,
                description=f"Relax Experience from {request.years_experience} yr → {suggested_exp} yr",
                recovered_count=recovered,
                field_key="years_experience"
            ))

    # E. Skill mode: AND -> OR
    if request.skills and len(request.skills) > 1 and request.skill_mode.upper() == "AND":
        norm_req = [normalize_skill(s) for s in request.skills if normalize_skill(s)]
        recovered = 0
        for cand in candidates:
            if cand.id in passing_candidates:
                continue
            other_failed = [f for f in failure_map[cand.id] if f["field"] != "skills"]
            if not other_failed:
                cand_s = candidate_skills.get(cand.id, set())
                # If they have ANY skill
                if any(s in cand_s for s in norm_req):
                    recovered += 1
        if recovered > 0:
            relaxation_suggestions.append(RelaxationSuggestion(
                filter_name="Skill Mode",
                current_value="AND",
                suggested_value="OR",
                description="Change skills mode from AND → OR",
                recovered_count=recovered,
                field_key="skill_mode"
            ))

    return WhatIfResponse(
        total_candidates=total_count,
        passing_candidates=len(passing_candidates),
        removed_candidates=removed_count,
        filters=funnel_stages,
        high_match_removed=high_match_removed,
        near_miss_candidates=near_miss_candidates,
        relaxation_suggestions=relaxation_suggestions
    )
