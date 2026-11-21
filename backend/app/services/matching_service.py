from typing import Dict, Any, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.skills_service import (
    normalize_skill,
    expand_skills_with_implications
)

def compute_candidate_match(candidate: Any, jd: Any) -> Dict[str, Any]:
    """
    Computes match score (0-100) and breakdown for candidate against a Job Description.
    Breakdown:
      - Skills (weight 50)
      - Experience fit (weight 25)
      - Education fit (weight 15)
      - TF-IDF text similarity (weight 10)
    """
    # 1. Prepare JD requirements
    jd_req_skills_raw = jd.required_skills or ""
    if isinstance(jd_req_skills_raw, str):
        jd_skills_list = [s.strip() for s in jd_req_skills_raw.split(",") if s.strip()]
    else:
        jd_skills_list = list(jd_req_skills_raw)

    jd_norm_skills = [normalize_skill(s) for s in jd_skills_list if normalize_skill(s)]
    jd_skills_set = set(jd_norm_skills)

    # 2. Prepare Candidate skills
    # Candidate skills can come from resume_text or extracted skills
    cand_text = candidate.resume_text or ""
    cand_skills_raw = getattr(candidate, "skills", None)
    if not cand_skills_raw:
        # Extract from evidence or text
        from app.services.skills_service import extract_skills_from_text
        cand_skills_list = extract_skills_from_text(cand_text)
    elif isinstance(cand_skills_raw, list):
        cand_skills_list = [normalize_skill(s) for s in cand_skills_raw if normalize_skill(s)]
    else:
        cand_skills_list = [normalize_skill(s.strip()) for s in str(cand_skills_raw).split(",") if normalize_skill(s.strip())]

    # Expand candidate skills with implied skills (e.g., Node.js implies JavaScript)
    expanded_cand_skills = set(expand_skills_with_implications(cand_skills_list))

    matched_skills = sorted(list(jd_skills_set.intersection(expanded_cand_skills)))
    missing_skills = sorted(list(jd_skills_set - expanded_cand_skills))

    # Weight 50: Skills match
    if jd_skills_set:
        skills_ratio = len(matched_skills) / len(jd_skills_set)
    else:
        skills_ratio = 1.0
    skills_score = round(skills_ratio * 50.0, 1)

    # Weight 25: Experience fit
    cand_exp = float(getattr(candidate, "years_experience", 0.0) or 0.0)
    jd_min_exp = float(getattr(jd, "min_experience", 0.0) or 0.0)

    if jd_min_exp <= 0.0:
        exp_score = 25.0
    elif cand_exp >= jd_min_exp:
        exp_score = 25.0
    else:
        # Partial credit proportional to exp
        exp_score = round((cand_exp / jd_min_exp) * 25.0, 1)

    # Weight 15: Education fit
    # Relevant engineering/tech degree awards full 15, other degrees get 10, none gets 5
    deg = (getattr(candidate, "degree", "") or "").lower()
    if any(k in deg for k in ["b.tech", "b.e", "bachelor of technology", "bachelor of engineering", "mca", "m.tech"]):
        edu_score = 15.0
    elif any(k in deg for k in ["b.sc", "bachelor", "master"]):
        edu_score = 12.0
    elif deg:
        edu_score = 10.0
    else:
        edu_score = 5.0

    # Weight 10: TF-IDF Text Similarity
    jd_desc = (jd.description or "") + " " + " ".join(jd_skills_list)
    tfidf_score = 0.0
    if cand_text.strip() and jd_desc.strip():
        try:
            vectorizer = TfidfVectorizer(stop_words="english")
            tfidf_matrix = vectorizer.fit_transform([cand_text, jd_desc])
            sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            tfidf_score = round(float(sim) * 10.0, 1)
        except Exception:
            tfidf_score = 5.0
    else:
        tfidf_score = 5.0

    total_score = round(skills_score + exp_score + edu_score + tfidf_score, 1)
    total_score = min(100.0, max(0.0, total_score))

    return {
        "match_score": total_score,
        "breakdown": {
            "skills_score": skills_score,
            "max_skills_score": 50.0,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "experience_score": exp_score,
            "max_experience_score": 25.0,
            "candidate_experience": cand_exp,
            "required_experience": jd_min_exp,
            "education_score": edu_score,
            "max_education_score": 15.0,
            "degree": getattr(candidate, "degree", None),
            "tfidf_score": tfidf_score,
            "max_tfidf_score": 10.0
        }
    }
