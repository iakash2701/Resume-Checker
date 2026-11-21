import io
import csv
from typing import List, Dict, Any, Optional

def sanitize_csv_cell(value: Any) -> str:
    """
    Prevents CSV formula injection by prepending a single quote if the cell begins with
    dangerous characters (=, +, -, @, \t, \r).
    Handles nulls and multiline text.
    """
    if value is None:
        return ""
    val_str = str(value)
    if not val_str:
        return ""

    first_char = val_str[0]
    if first_char in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + val_str
    return val_str

def generate_candidates_csv(candidates_data: List[Dict[str, Any]]) -> str:
    """
    Generates a RFC 4180 compliant CSV string with UTF-8 encoding support and security sanitization.
    """
    fieldnames = [
        "Candidate Name",
        "Email",
        "Phone",
        "Location",
        "Degree",
        "College",
        "10th %",
        "12th %",
        "CGPA",
        "Experience",
        "Graduation Year",
        "Skills",
        "JD Match Score",
        "Matched Skills",
        "Missing Skills",
        "Current Stage",
        "Parsing Confidence"
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()

    for cand in candidates_data:
        row = {
            "Candidate Name": sanitize_csv_cell(cand.get("name")),
            "Email": sanitize_csv_cell(cand.get("email")),
            "Phone": sanitize_csv_cell(cand.get("phone")),
            "Location": sanitize_csv_cell(cand.get("location")),
            "Degree": sanitize_csv_cell(cand.get("degree")),
            "College": sanitize_csv_cell(cand.get("college")),
            "10th %": sanitize_csv_cell(cand.get("tenth_pct")),
            "12th %": sanitize_csv_cell(cand.get("twelfth_pct")),
            "CGPA": sanitize_csv_cell(cand.get("cgpa_10")),
            "Experience": sanitize_csv_cell(cand.get("years_experience")),
            "Graduation Year": sanitize_csv_cell(cand.get("grad_year")),
            "Skills": sanitize_csv_cell(", ".join(cand.get("skills", []))),
            "JD Match Score": sanitize_csv_cell(cand.get("match_score")),
            "Matched Skills": sanitize_csv_cell(", ".join(cand.get("matched_skills", []))),
            "Missing Skills": sanitize_csv_cell(", ".join(cand.get("missing_skills", []))),
            "Current Stage": sanitize_csv_cell(cand.get("pipeline_stage")),
            "Parsing Confidence": sanitize_csv_cell(cand.get("confidence", "verified" if cand.get("is_verified") else "standard"))
        }
        writer.writerow(row)

    return output.getvalue()
