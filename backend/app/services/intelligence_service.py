import re
from typing import List, Dict, Any, Optional, Tuple
from app.services.skills_service import normalize_skill, extract_skills_from_text
from app.models import Candidate, JobDescription

# Predefined structured interview probe templates based on skill category and claim strength
INTERVIEW_PROBE_TEMPLATES = {
    "python": {
        "strong": "In your Python project, what design patterns or architecture choices did you make to ensure code maintainability?",
        "weak": "Can you walk us through a Python script or application you wrote from scratch, detailing the libraries used?"
    },
    "sql": {
        "strong": "Can you describe a query optimization or complex multi-table JOIN scenario you worked through and how you indexed it?",
        "weak": "Describe a SQL query you used for data extraction/analysis and explain what business question it answered."
    },
    "docker": {
        "strong": "How did you optimize your Docker images for multi-stage builds and layer caching in production CI/CD?",
        "weak": "Can you explain how you used Docker in one of your projects, including writing a Dockerfile or running docker-compose?"
    },
    "fastapi": {
        "strong": "How did you manage asynchronous request handling, dependency injection, and Pydantic validation in FastAPI?",
        "weak": "What endpoints did you construct using FastAPI, and how did you test their request/response schemas?"
    },
    "react": {
        "strong": "How did you architect client-side state management and minimize unnecessary re-renders in your React component hierarchy?",
        "weak": "Can you describe how components, hooks (e.g. useState/useEffect), and API integration were structured in your React project?"
    },
    "node.js": {
        "strong": "How did you handle backpressure or concurrent I/O operations in your Node.js event-loop services?",
        "weak": "Describe an Express or HTTP service you built with Node.js and how database connections were handled."
    },
    "aws": {
        "strong": "Which specific AWS services (EC2, S3, Lambda, RDS) did you configure and how did you manage IAM security policies?",
        "weak": "Have you directly deployed applications to AWS, and what was your experience managing cloud resources?"
    },
    "kubernetes": {
        "strong": "How did you handle Pod scheduling, resource quotas, and ingress traffic management across K8s namespaces?",
        "weak": "What Kubernetes resources (Deployments, Services, ConfigMaps) have you defined and deployed?"
    },
    "power bi": {
        "strong": "What complex DAX measures or star-schema data modeling did you build to handle large analytics dashboards?",
        "weak": "Describe a Power BI dashboard you created and how you transformed the underlying data source."
    },
    "machine learning": {
        "strong": "How did you prevent data leakage, validate your feature pipeline, and measure business evaluation metrics?",
        "weak": "Which machine learning algorithms did you evaluate for your project, and what feature engineering steps did you perform?"
    }
}

DEFAULT_PROBE_TEMPLATE = {
    "strong": "In your experience applying {skill}, what was the most challenging technical roadblock you encountered and how did you resolve it?",
    "weak": "Your profile references {skill}. Can you explain how you applied this skill in a hands-on academic or work project?"
}

def analyze_skill_gap(candidate: Candidate, jd: JobDescription) -> Dict[str, Any]:
    """
    Computes deterministic Skill Gap analysis:
    - Matched required skills
    - Missing required skills
    - Matched nice-to-have skills
    - Missing nice-to-have skills
    - Skill coverage percentage = (matched required / total required) * 100
    """
    candidate_skills = set(extract_skills_from_text(candidate.resume_text or ""))
    
    req_raw = [s.strip() for s in (jd.required_skills or "").split(",") if s.strip()]
    nice_raw = [s.strip() for s in (jd.nice_to_have_skills or "").split(",") if s.strip()]

    # Normalize JD skills
    req_normalized = [normalize_skill(s) for s in req_raw if normalize_skill(s)]
    nice_normalized = [normalize_skill(s) for s in nice_raw if normalize_skill(s)]

    matched_required = [s for s in req_normalized if s in candidate_skills]
    missing_required = [s for s in req_normalized if s not in candidate_skills]

    matched_nice = [s for s in nice_normalized if s in candidate_skills]
    missing_nice = [s for s in nice_normalized if s not in candidate_skills]

    total_req = len(req_normalized)
    skill_coverage = round((len(matched_required) / total_req * 100), 1) if total_req > 0 else 100.0

    return {
        "total_required": total_req,
        "matched_required": matched_required,
        "missing_required": missing_required,
        "matched_nice": matched_nice,
        "missing_nice": missing_nice,
        "skill_coverage_pct": skill_coverage,
        "all_candidate_skills": sorted(list(candidate_skills))
    }

def find_evidence_snippet(skill: str, text: str) -> Optional[Tuple[str, str]]:
    """
    Extracts evidence sentence/paragraph for a skill from resume text.
    Returns (snippet, source_type) where source_type is 'Project Experience', 'Work Experience', or 'Skills Section'.
    """
    skill_lower = skill.lower()
    lines = text.split("\n")
    current_section = "General Profile"

    # Common section markers
    for i, line in enumerate(lines):
        line_clean = line.strip().lower()
        if any(h in line_clean for h in ["project", "academic project", "key projects"]):
            current_section = "Project Experience"
        elif any(h in line_clean for h in ["experience", "internship", "employment", "work history"]):
            current_section = "Work Experience"
        elif any(h in line_clean for h in ["skills", "technical skills", "technologies", "competencies"]):
            current_section = "Skills Section"

        # Check if skill is in this line or sentence
        if re.search(rf"\b{re.escape(skill_lower)}\b", line.lower()):
            snippet = line.strip()
            # If the snippet is just "Python" or "Skills: Python, SQL"
            if len(snippet.split()) <= 4 or current_section == "Skills Section":
                # Check if neighboring lines have more descriptive context
                surrounding = " ".join([l.strip() for l in lines[max(0, i-1):min(len(lines), i+2)] if l.strip()])
                if len(surrounding) > len(snippet) and current_section != "Skills Section":
                    return surrounding[:220], current_section
                return snippet[:180], current_section
            return snippet[:220], current_section

    return None

def analyze_hiring_intelligence(candidate: Candidate, jd: Optional[JobDescription] = None) -> Dict[str, Any]:
    """
    Builds structured Evidence-Based Hiring Intelligence:
    1. Skill-by-skill claim breakdown:
       - Skill name
       - Status (Matched / Claimed weak / Missing)
       - Evidence source (Project Experience, Work Experience, Skills List, None)
       - Evidence text
       - Confidence (HIGH, MEDIUM, LOW)
       - Interview Probe
    2. Evidence Strength Score (0-100) & Explainable breakdown
    3. Visual Evidence Graph chains
    """
    resume_text = candidate.resume_text or ""
    candidate_skills = set(extract_skills_from_text(resume_text))

    target_skills = []
    if jd:
        req_raw = [s.strip() for s in (jd.required_skills or "").split(",") if s.strip()]
        for r in req_raw:
            norm = normalize_skill(r)
            if norm and norm not in target_skills:
                target_skills.append(norm)
    
    # If no JD or to complement, add candidate's own top skills
    for s in candidate_skills:
        if s not in target_skills:
            target_skills.append(s)

    evidence_items = []
    strong_evidence_count = 0
    weak_evidence_count = 0
    missing_count = 0
    strong_list = []
    weak_list = []
    missing_list = []
    evidence_graph = []

    for skill in target_skills:
        skill_key = skill.lower()
        probe_dict = INTERVIEW_PROBE_TEMPLATES.get(skill_key, DEFAULT_PROBE_TEMPLATE)

        if skill not in candidate_skills:
            # Skill not found in candidate
            missing_count += 1
            missing_list.append(skill)
            evidence_items.append({
                "skill": skill,
                "status": "Missing",
                "confidence": "LOW",
                "source_type": "None",
                "evidence_snippet": f"No mention or supporting evidence found in candidate profile or resume for {skill}.",
                "interview_probe": f"Have you had any exposure to {skill} or related technologies, even in self-study or coursework?"
            })
            evidence_graph.append({
                "skill": skill,
                "status": "Missing",
                "nodes": [
                    {"label": "JD Requirement", "detail": "Required", "type": "requirement"},
                    {"label": "Resume Match", "detail": "Not found in profile", "type": "missing"}
                ]
            })
            continue

        # Candidate claims or has skill
        res_ev = find_evidence_snippet(skill, resume_text)
        if res_ev:
            snippet, source_type = res_ev
            # Differentiate strong vs weak evidence
            # Strong: present in Project Experience or Work Experience with substantive text
            if source_type in ["Project Experience", "Work Experience"] and len(snippet.split()) >= 6:
                confidence = "HIGH"
                strong_evidence_count += 1
                strong_list.append(f"{skill} ({source_type})")
                probe = probe_dict.get("strong", DEFAULT_PROBE_TEMPLATE["strong"]).format(skill=skill)
                status = "Strong Evidence"
            elif source_type == "Skills Section" or len(snippet.split()) < 6:
                confidence = "LOW"
                weak_evidence_count += 1
                weak_list.append(f"{skill} (Listed without supporting project details)")
                probe = probe_dict.get("weak", DEFAULT_PROBE_TEMPLATE["weak"]).format(skill=skill)
                status = "Weak Claim"
            else:
                confidence = "MEDIUM"
                strong_evidence_count += 0.5
                probe = probe_dict.get("strong", DEFAULT_PROBE_TEMPLATE["strong"]).format(skill=skill)
                status = "Moderate Evidence"
        else:
            confidence = "LOW"
            weak_evidence_count += 1
            source_type = "Implicit Keyword"
            snippet = f"Keyword detected in resume body but lacks dedicated project or experience context."
            probe = probe_dict.get("weak", DEFAULT_PROBE_TEMPLATE["weak"]).format(skill=skill)
            status = "Weak Claim"
            weak_list.append(f"{skill} (Keyword only)")

        evidence_items.append({
            "skill": skill,
            "status": status,
            "confidence": confidence,
            "source_type": source_type,
            "evidence_snippet": snippet,
            "interview_probe": probe
        })

        # Build Graph chain for UI
        graph_nodes = []
        if jd:
            graph_nodes.append({"label": "JD Requirement", "detail": "Required Skill", "type": "requirement"})
        graph_nodes.append({"label": f"Skill: {skill}", "detail": status, "type": "skill"})
        graph_nodes.append({"label": f"Context: {source_type}", "detail": snippet[:100] + ("..." if len(snippet) > 100 else ""), "type": "evidence"})
        graph_nodes.append({"label": "Interview Probe", "detail": probe, "type": "probe"})

        evidence_graph.append({
            "skill": skill,
            "status": status,
            "nodes": graph_nodes
        })

    # Evidence Score Calculation (0-100)
    total_evaluated = len(target_skills) if target_skills else 1
    # Weight: Strong evidence gives 100%, Medium 60%, Weak 30%, Missing 0%
    score_points = (strong_evidence_count * 100.0) + (weak_evidence_count * 30.0)
    evidence_score = round(min(100.0, score_points / total_evaluated), 1)

    return {
        "evidence_score": evidence_score,
        "evidence_items": evidence_items,
        "strong_evidence": strong_list,
        "weak_evidence": weak_list,
        "missing_evidence": missing_list,
        "evidence_graph": evidence_graph
    }
