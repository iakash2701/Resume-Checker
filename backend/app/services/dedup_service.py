import re
from typing import List, Dict, Any, Optional, Tuple
from rapidfuzz import fuzz
from sqlalchemy.orm import Session
from app.models import Candidate

def normalize_string(s: Optional[str]) -> str:
    if not s:
        return ""
    return re.sub(r"[^a-z0-9]", "", s.lower())

def normalize_phone(phone: Optional[str]) -> str:
    if not phone:
        return ""
    # Keep last 10 digits
    digits = re.sub(r"\D", "", phone)
    return digits[-10:] if len(digits) >= 10 else digits

def compute_candidate_similarity(c1: Candidate, c2: Candidate) -> Dict[str, Any]:
    """
    Computes multi-signal similarity between two candidates.
    Signals:
    - Email exact match (100% signal)
    - Phone exact match (100% signal)
    - Candidate name similarity (rapidfuzz token_sort_ratio)
    - Resume text similarity (rapidfuzz partial_ratio / token_set_ratio)
    - College / Degree overlap
    - Experience overlap
    """
    reasons = []
    
    # 1. Email check
    email1 = (c1.email or "").strip().lower()
    email2 = (c2.email or "").strip().lower()
    same_email = bool(email1 and email2 and email1 == email2)
    if same_email:
        reasons.append("Identical email address")

    # 2. Phone check
    p1 = normalize_phone(c1.phone)
    p2 = normalize_phone(c2.phone)
    same_phone = bool(p1 and p2 and p1 == p2)
    if same_phone:
        reasons.append("Identical phone number")

    # 3. Name similarity
    name1 = (c1.name or "").strip().lower()
    name2 = (c2.name or "").strip().lower()
    name_sim = fuzz.token_sort_ratio(name1, name2) if (name1 and name2) else 0.0

    # 4. Resume text similarity
    txt1 = (c1.resume_text or "").strip()
    txt2 = (c2.resume_text or "").strip()
    if txt1 and txt2:
        # Use token_set_ratio which is resilient to section reordering
        text_sim = float(fuzz.token_set_ratio(txt1[:2500], txt2[:2500]))
    else:
        text_sim = 0.0

    # 5. Education & Experience overlap
    col1 = normalize_string(c1.college)
    col2 = normalize_string(c2.college)
    same_college = bool(col1 and col2 and (col1 in col2 or col2 in col1 or fuzz.ratio(col1, col2) > 85))
    if same_college:
        reasons.append(f"Same college ({c1.college})")

    same_grad = bool(c1.grad_year and c2.grad_year and c1.grad_year == c2.grad_year)
    if same_grad:
        reasons.append(f"Same graduation year ({c1.grad_year})")

    exp_diff = abs((c1.years_experience or 0.0) - (c2.years_experience or 0.0))
    if exp_diff <= 0.5:
        reasons.append("Similar years of experience")

    # Overall similarity calculation
    if same_email or same_phone:
        if name_sim >= 75 or text_sim >= 70:
            classification = "EXACT DUPLICATE"
            overall_sim = max(95.0, round((name_sim * 0.4) + (text_sim * 0.6), 1))
        else:
            classification = "LIKELY DUPLICATE"
            overall_sim = max(85.0, round((name_sim * 0.5) + (text_sim * 0.5), 1))
    else:
        # Weighted score
        weighted = (name_sim * 0.45) + (text_sim * 0.35)
        if same_college:
            weighted += 10.0
        if same_grad:
            weighted += 5.0
        if exp_diff <= 0.3:
            weighted += 5.0
        overall_sim = min(100.0, round(weighted, 1))

        if overall_sim >= 88.0:
            classification = "LIKELY DUPLICATE"
            reasons.append(f"High resume content & profile match ({overall_sim}%)")
        else:
            classification = "UNIQUE"

    if text_sim >= 85:
        reasons.append(f"{round(text_sim)}% text similarity")
    if name_sim >= 90:
        reasons.append(f"Matching name ({c1.name})")

    return {
        "candidate_id": c2.id,
        "name": c2.name,
        "email": c2.email,
        "college": c2.college,
        "similarity_score": round(overall_sim, 1),
        "classification": classification,
        "reasons": reasons if reasons else ["No significant matching signals"]
    }

def find_duplicates_for_candidate(candidate: Candidate, db: Session, threshold: float = 75.0) -> List[Dict[str, Any]]:
    """
    Checks a candidate against all existing candidates in DB.
    Returns list of matches sorted by similarity descending.
    """
    existing_candidates = db.query(Candidate).filter(Candidate.id != candidate.id).all()
    matches = []
    
    for other in existing_candidates:
        res = compute_candidate_similarity(candidate, other)
        if res["similarity_score"] >= threshold or res["classification"] != "UNIQUE":
            matches.append(res)
            
    matches.sort(key=lambda x: x["similarity_score"], reverse=True)
    return matches
