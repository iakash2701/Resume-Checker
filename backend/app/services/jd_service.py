import re
from typing import Dict, Any, List
from app.services.skills_service import (
    normalize_skill,
    extract_skills_from_text,
    expand_skills_with_implications
)

def parse_job_description_text(text: str, title: str = "Untitled Role") -> Dict[str, Any]:
    """
    Extracts title, required skills, nice-to-have skills, and min experience from pasted text.
    """
    if not text:
        return {
            "title": title,
            "description": "",
            "min_experience": 0.0,
            "required_skills": [],
            "nice_to_have_skills": []
        }

    # Experience extraction
    min_exp = 0.0
    exp_match = re.search(r"(?:min(?:imum)?|at\s+least)?\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+(?:of\s+)?experience)?", text, flags=re.IGNORECASE)
    if exp_match:
        try:
            min_exp = float(exp_match.group(1))
        except ValueError:
            min_exp = 0.0

    # Section extraction: Required vs Nice-to-have
    required_skills = set()
    nice_to_have_skills = set()

    lines = text.split("\n")
    current_section = "general"

    req_section_lines = []
    nice_section_lines = []

    for line in lines:
        lower_line = line.strip().lower()
        if any(h in lower_line for h in ["preferred", "nice to have", "plus", "bonus", "good to have", "optional"]):
            current_section = "nice"
            continue
        elif any(h in lower_line for h in ["required", "must have", "requirements", "qualifications", "skills"]):
            current_section = "required"
            continue

        if current_section == "nice":
            nice_section_lines.append(line)
        elif current_section == "required":
            req_section_lines.append(line)

    if nice_section_lines:
        nice_extracted = extract_skills_from_text("\n".join(nice_section_lines))
        nice_to_have_skills.update(nice_extracted)

    if req_section_lines:
        req_extracted = extract_skills_from_text("\n".join(req_section_lines))
        required_skills.update(req_extracted)

    # If no explicit sections were found, extract from the whole text
    if not required_skills and not nice_to_have_skills:
        all_skills = extract_skills_from_text(text)
        required_skills.update(all_skills)

    # Clean duplicates: required takes priority
    nice_to_have_skills = nice_to_have_skills - required_skills

    return {
        "title": title,
        "description": text.strip(),
        "min_experience": min_exp,
        "required_skills": sorted(list(required_skills)),
        "nice_to_have_skills": sorted(list(nice_to_have_skills))
    }
