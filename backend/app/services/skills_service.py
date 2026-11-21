import os
import json
import re
from typing import Dict, List, Set, Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))
SKILLS_JSON_PATH = os.path.join(BASE_DIR, "skills.json")

_ALIAS_TO_CANONICAL: Dict[str, str] = {}
_IMPLIED_SKILLS: Dict[str, List[str]] = {}
_CANONICAL_SKILLS: Set[str] = set()

def _load_skill_map():
    global _ALIAS_TO_CANONICAL, _IMPLIED_SKILLS, _CANONICAL_SKILLS
    if _ALIAS_TO_CANONICAL:
        return

    path = SKILLS_JSON_PATH
    if not os.path.exists(path):
        # Fallback to relative path lookup
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/skills.json"))

    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    skills_data = data.get("skills", {})
    for canonical, details in skills_data.items():
        _CANONICAL_SKILLS.add(canonical)
        _ALIAS_TO_CANONICAL[canonical.lower()] = canonical
        for alias in details.get("aliases", []):
            _ALIAS_TO_CANONICAL[alias.lower().strip()] = canonical
        _IMPLIED_SKILLS[canonical] = details.get("implies", [])

_load_skill_map()

def normalize_skill(skill_str: str) -> Optional[str]:
    """
    Normalizes any skill name or alias into its canonical form.
    E.g., 'reactjs', 'React.js', 'react' -> 'React'
          'k8s' -> 'Kubernetes'
          'postgres' -> 'PostgreSQL'
    """
    _load_skill_map()
    if not skill_str:
        return None
    cleaned = skill_str.strip().lower()
    return _ALIAS_TO_CANONICAL.get(cleaned, skill_str.strip())

def get_canonical_skills() -> Set[str]:
    _load_skill_map()
    return _CANONICAL_SKILLS

def expand_skills_with_implications(skills: List[str]) -> List[str]:
    """
    Expands a skill list with implied skills recursively.
    E.g., ['Node.js'] -> ['Node.js', 'JavaScript']
          ['FastAPI'] -> ['FastAPI', 'Python', 'REST API']
    """
    _load_skill_map()
    result_set = set()
    to_process = list(skills)

    while to_process:
        curr = to_process.pop(0)
        norm = normalize_skill(curr)
        if norm and norm not in result_set:
            result_set.add(norm)
            implied = _IMPLIED_SKILLS.get(norm, [])
            for imp in implied:
                if imp not in result_set:
                    to_process.append(imp)

    return sorted(list(result_set))

def extract_skills_from_text(text: str) -> List[str]:
    """
    Extracts all known skills and aliases from raw text and returns normalized canonical list.
    """
    _load_skill_map()
    if not text:
        return []

    found_skills = set()
    text_lower = text.lower()

    # Sort aliases by length descending so longer phrases match first (e.g. 'react js' before 'js')
    sorted_aliases = sorted(_ALIAS_TO_CANONICAL.keys(), key=lambda x: len(x), reverse=True)

    for alias in sorted_aliases:
        # Regex boundary check
        # For special characters like c++, c#, .net
        escaped = re.escape(alias)
        pattern = r"(?<![\w\.\+#])" + escaped + r"(?![\w\.\+#])"
        if re.search(pattern, text_lower):
            canonical = _ALIAS_TO_CANONICAL[alias]
            found_skills.add(canonical)

    return sorted(list(found_skills))
