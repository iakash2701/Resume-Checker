import re
import os
from typing import Dict, Any, Optional, List, Tuple
import pdfplumber
from docx import Document

DEGREE_PATTERNS = [
    r"B\.?Tech(?:\s+(?:Artificial\s+Intelligence(?:\s+and\s+Machine\s+Learning)?|AIML|Information\s+Technology|Computer\s+Science(?:\s+and\s+Engineering)?|Mechanical|Civil))?",
    r"B\.?E\.?(?:\s+(?:Computer\s+Science(?:\s+Engineering)?|Electronics\s+and\s+Communication(?:\s+Engineering)?|Information\s+Technology|Mechanical))?",
    r"Bachelor\s+of\s+Technology(?:\s+(?:in\s+)?[\w\s]+)?",
    r"Bachelor\s+of\s+Engineering(?:\s*-\s*[\w\s]+|\s+(?:in\s+)?[\w\s]+)?",
    r"MCA|Master\s+of\s+Computer\s+Applications",
    r"B\.?Sc(?:\s+Computer\s+Science|\s+Information\s+Technology)?",
    r"M\.?Tech(?:\s+[\w\s]+)?",
    r"MBA"
]

COLLEGE_KEYWORDS = [
    "PSG College of Technology",
    "PSG Tech",
    "Thiagarajar College of Engineering",
    "Vellore Institute of Technology",
    "VIT",
    "Bannari Amman Institute of Technology",
    "SSN College of Engineering",
    "Coimbatore Institute of Technology",
    "Amrita Vishwa Vidyapeetham",
    "Kongu Engineering College",
    "Kumaraguru College of Technology",
    "Sri Krishna College of Engineering and Technology",
    "RV College of Engineering",
    "PES University",
    "SRM Institute of Science and Technology",
    "Manipal Institute of Technology"
]

SKILLS_VOCABULARY = [
    "Python", "Java", "JavaScript", "TypeScript", "React", "React.js",
    "Node", "Node.js", "SQL", "MySQL", "PostgreSQL", "MongoDB",
    "FastAPI", "Django", "Flask", "Power BI", "Tableau",
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
    "Docker", "AWS", "Git", "GitHub", "Linux", "HTML", "CSS"
]

TENTH_PATTERN_KEYWORDS = [
    r"10th\s+Standard", r"10th\s+Grade", r"10th", r"Class\s+X", r"Xth\s+Standard", r"Xth",
    r"SSC\s+Board", r"SSC", r"Matriculation\s+Examination", r"Matriculation",
    r"Secondary\s+School\s+Certificate", r"Secondary\s+School"
]

TWELFTH_PATTERN_KEYWORDS = [
    r"12th\s+Standard", r"12th", r"Class\s+XII", r"XIIth\s+Standard", r"XIIth", r"XII",
    r"HSC\s+Examination", r"HSC", r"Higher\s+Secondary",
    r"Intermediate\s+Board", r"Intermediate",
    r"Senior\s+Secondary\s+Certificate", r"Senior\s+Secondary"
]


def extract_text(file_path: str) -> str:
    """Extract raw text from PDF or DOCX file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    elif ext == ".docx":
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

    return text.strip()


def extract_contact_information(text: str) -> Dict[str, Optional[str]]:
    """Extract candidate name, email, phone, location."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    name = None
    email = None
    phone = None
    location = None

    # First line often contains name
    if lines:
        first_line = lines[0]
        # Clean up header styling
        first_line = re.sub(r"^(?:RESUME|CURRICULUM VITAE|CV)\s*[:-]?\s*", "", first_line, flags=re.IGNORECASE).strip()
        if len(first_line) > 1 and len(first_line) < 60 and not any(k in first_line.lower() for k in ["email", "phone", "http", "@"]):
            # Capitalize properly if all upper
            if first_line.isupper():
                name = first_line.title()
            else:
                name = first_line

    # Email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if email_match:
        email = email_match.group(0).strip()

    # Phone - Indian phone patterns (+91 XXXXXXXXXX or 10 digits)
    phone_match = re.search(r"(?:\+91[\s-]?)?[6-9]\d{9}", text)
    if phone_match:
        phone = phone_match.group(0).strip()

    # Location
    loc_match = re.search(r"Location:\s*([^\|\n\r]+)", text, flags=re.IGNORECASE)
    if loc_match:
        location = loc_match.group(1).strip()
    else:
        # Fallback check for major cities
        city_match = re.search(r"\b(Bengaluru|Bangalore|Chennai|Hyderabad|Coimbatore|Pune|Kochi|Mumbai|Delhi|Noida)\b", text, flags=re.IGNORECASE)
        if city_match:
            location = city_match.group(1)

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "location": location
    }


def extract_academic_information(text: str) -> Dict[str, Any]:
    """Extract degree, college, grad_year, 10th %, 12th %, and CGPA with evidence."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    degree = None
    college = None
    grad_year = None
    tenth_data = {"value": None, "confidence": "low", "source_text": ""}
    twelfth_data = {"value": None, "confidence": "low", "source_text": ""}
    cgpa_data = {"value": None, "confidence": "low", "source_text": ""}

    # 1. Degree
    for pattern in DEGREE_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            degree = match.group(0).strip()
            # Clean up trailing parentheses if present
            degree = re.sub(r"\s*\([^)]*\)$", "", degree).strip()
            break

    # 2. College
    for inst in COLLEGE_KEYWORDS:
        if re.search(r"\b" + re.escape(inst) + r"\b", text, flags=re.IGNORECASE):
            # Check if there is a more detailed line
            for line in lines:
                if inst.lower() in line.lower():
                    # Institution: ...
                    m = re.search(r"Institution:\s*(.+)", line, flags=re.IGNORECASE)
                    if m:
                        college = m.group(1).strip()
                    else:
                        college = line.strip()
                    break
            if not college:
                college = inst
            break

    # 3. Graduation Year
    # Support formats: 2024-2028, Class of 2028, Graduation: 2028, Graduating in 2028, (2028)
    year_range_match = re.search(r"\b(20\d{2})\s*[-–—]\s*(20\d{2})\b", text)
    if year_range_match:
        grad_year = int(year_range_match.group(2))
    else:
        year_match = re.search(r"(?:Graduation|Graduating\s+in|Class\s+of|Batch\s+of|Year\s+of\s+Passing)[\s:]*(202[0-9])\b", text, flags=re.IGNORECASE)
        if year_match:
            grad_year = int(year_match.group(1))
        else:
            # Look near education lines for 2024-2029
            edu_year_match = re.search(r"(?:EDUCATION|B\.?Tech|B\.?E\.?|MCA|B\.?Sc)[\s\S]{1,100}?\b(202[4-9])\b", text, flags=re.IGNORECASE)
            if edu_year_match:
                grad_year = int(edu_year_match.group(1))

    # Helper to parse percentage from string
    def parse_pct_val(val_str: str) -> Optional[float]:
        try:
            return round(float(val_str.strip()), 2)
        except ValueError:
            return None

    # 4. 10th Percentage & 12th Percentage
    # We inspect line by line to maintain tight contextual grouping
    for line in lines:
        # Check 10th
        tenth_kw_matched = None
        for kw in TENTH_PATTERN_KEYWORDS:
            if re.search(r"\b" + kw + r"\b", line, flags=re.IGNORECASE):
                tenth_kw_matched = kw
                break

        if tenth_kw_matched:
            # Look for number followed by % or percentage/scored
            m = re.search(r"(?:scored\s+)?(\d{1,2}(?:\.\d{1,2})?)\s*(?:%|\s*percent|\s*Percentage)", line, flags=re.IGNORECASE)
            if not m:
                m = re.search(r"[:\-\s]+(\d{1,2}(?:\.\d{1,2})?)\s*%", line)
            if not m:
                m = re.search(r"Percentage:\s*(\d{1,2}(?:\.\d{1,2})?)", line, flags=re.IGNORECASE)
            
            if m:
                val = parse_pct_val(m.group(1))
                if val is not None and 35.0 <= val <= 100.0:
                    confidence = "high" if ("%" in line or "percent" in line.lower() or "percentage" in line.lower()) else "medium"
                    tenth_data = {
                        "value": val,
                        "confidence": confidence,
                        "source_text": line.strip()
                    }

        # Check 12th
        twelfth_kw_matched = None
        for kw in TWELFTH_PATTERN_KEYWORDS:
            if re.search(r"\b" + kw + r"\b", line, flags=re.IGNORECASE):
                twelfth_kw_matched = kw
                break

        if twelfth_kw_matched:
            m = re.search(r"(?:scored\s+)?(\d{1,2}(?:\.\d{1,2})?)\s*(?:%|\s*percent|\s*Percentage)", line, flags=re.IGNORECASE)
            if not m:
                m = re.search(r"[:\-\s]+(\d{1,2}(?:\.\d{1,2})?)\s*%", line)
            if not m:
                m = re.search(r"Percentage:\s*(\d{1,2}(?:\.\d{1,2})?)", line, flags=re.IGNORECASE)

            if m:
                val = parse_pct_val(m.group(1))
                if val is not None and 35.0 <= val <= 100.0:
                    confidence = "high" if ("%" in line or "percent" in line.lower() or "percentage" in line.lower()) else "medium"
                    twelfth_data = {
                        "value": val,
                        "confidence": confidence,
                        "source_text": line.strip()
                    }

    # 5. CGPA Normalization
    # Check for 4-point scale: e.g. 3.4/4.0, GPA: 3.4/4, 3.4 / 4.0 GPA, 3.85 on a 4.0 scale
    four_scale_pattern = r"(?:GPA|CGPA|Grade\s+Point\s+Average)?[\s:\-]*(\d(?:\.\d{1,2})?)\s*(?:/\s*4(?:\.0)?|\s+on\s+a\s+4(?:\.0)?\s+scale)|\b(\d\.\d{1,2})\s*/\s*4(?:\.0)?\s*GPA"
    four_match = re.search(four_scale_pattern, text, flags=re.IGNORECASE)
    
    if four_match:
        val_str = four_match.group(1) or four_match.group(2)
        try:
            val_4 = float(val_str)
            if 1.0 <= val_4 <= 4.0:
                normalized_cgpa = round((val_4 / 4.0) * 10.0, 2)
                # Find matching line for source snippet
                src_line = next((l for l in lines if val_str in l), four_match.group(0))
                cgpa_data = {
                    "value": normalized_cgpa,
                    "confidence": "high",
                    "source_text": src_line.strip()
                }
        except ValueError:
            pass

    # If not 4-point scale, check for 10-point scale / ambiguous
    if cgpa_data["value"] is None:
        # Pattern 1: explicit /10 (e.g. CGPA: 8.2/10, 8.2 / 10, 8.2/10, 8.2 out of 10)
        ten_scale_match = re.search(r"(?:(?:CGPA|GPA|Cumulative\s+GPA|Grade\s+Point\s+Average)[\s:\-]*)?(\d{1,2}(?:\.\d{1,2})?)\s*(?:/\s*10(?:\.0)?|\s+out\s+of\s+10)", text, flags=re.IGNORECASE)
        if ten_scale_match:
            try:
                val_10 = float(ten_scale_match.group(1))
                if 4.0 <= val_10 <= 10.0:
                    src_line = next((l for l in lines if ten_scale_match.group(1) in l and ("10" in l or "CGPA" in l)), ten_scale_match.group(0))
                    cgpa_data = {
                        "value": round(val_10, 2),
                        "confidence": "high",
                        "source_text": src_line.strip()
                    }
            except ValueError:
                pass

    if cgpa_data["value"] is None:
        # Pattern 2: CGPA: 8.2 or CGPA - 7.9 or 8.2 CGPA
        cgpa_label_match = re.search(r"(?:CGPA|GPA|Cumulative\s+GPA)[\s:\-]+(\d{1,2}(?:\.\d{1,2})?)\b|\b(\d{1,2}(?:\.\d{1,2})?)\s*(?:CGPA|GPA)\b", text, flags=re.IGNORECASE)
        if cgpa_label_match:
            val_str = cgpa_label_match.group(1) or cgpa_label_match.group(2)
            try:
                val = float(val_str)
                # Distinguish from percentage (usually percentages are > 30 and have %)
                if 4.0 <= val <= 10.0:
                    src_line = next((l for l in lines if val_str in l and ("cgpa" in l.lower() or "gpa" in l.lower())), cgpa_label_match.group(0))
                    cgpa_data = {
                        "value": round(val, 2),
                        "confidence": "high" if "cgpa" in src_line.lower() else "medium",
                        "source_text": src_line.strip()
                    }
            except ValueError:
                pass

    if cgpa_data["value"] is None:
        # Pattern 3: Ambiguous score like "Academic Score: 8.2"
        ambig_match = re.search(r"(?:Academic\s+Score|Overall\s+Score|Score)[\s:\-]+(\d{1,2}(?:\.\d{1,2})?)\b", text, flags=re.IGNORECASE)
        if ambig_match:
            try:
                val = float(ambig_match.group(1))
                if 4.0 <= val <= 10.0:
                    src_line = next((l for l in lines if ambig_match.group(1) in l), ambig_match.group(0))
                    cgpa_data = {
                        "value": round(val, 2),
                        "confidence": "low",
                        "source_text": src_line.strip()
                    }
            except ValueError:
                pass

    return {
        "degree": degree,
        "college": college,
        "grad_year": grad_year,
        "tenth": tenth_data,
        "twelfth": twelfth_data,
        "cgpa": cgpa_data
    }


def extract_experience(text: str) -> float:
    """Extract years of experience as float."""
    # Fresher check
    if re.search(r"\b(?:Fresher|Entry\s*Level|No\s+prior\s+experience)\b", text, flags=re.IGNORECASE):
        # Ensure they don't also list full-time years
        if not re.search(r"\b(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s+of\s+(?:professional|work)\s+experience\b", text, flags=re.IGNORECASE):
            return 0.0

    # Month patterns: e.g. "6 months internship experience", "Worked for 18 months"
    month_match = re.search(r"(\d+)\s*(?:months|mo|mths)\b", text, flags=re.IGNORECASE)
    if month_match:
        months = int(month_match.group(1))
        # Ignore age or graduation duration ranges like 48 months
        if months <= 60:
            return round(months / 12.0, 1)

    # Year patterns: e.g. "1 year experience", "Experience: 1 year", "1.5 years experience", "Experience: 2 years", "Over 3 years", "3.0 years in software engineering"
    year_match = re.search(r"(?:Experience|Worked|Total\s+Experience)[\s:\-]*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b", text, flags=re.IGNORECASE)
    if not year_match:
        year_match = re.search(r"(?:Over\s+)?(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s+(?:of\s+|in\s+)?(?:professional|full-time|relevant|software|work)?\s*(?:engineering|experience)?\b", text, flags=re.IGNORECASE)

    if year_match:
        try:
            return round(float(year_match.group(1)), 1)
        except ValueError:
            pass

    return 0.0


def extract_skills(text: str) -> List[str]:
    """Extract skills matching known vocabulary."""
    extracted = []
    text_lower = text.lower()

    for skill in SKILLS_VOCABULARY:
        # Exact boundary or special characters match
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
        if re.search(pattern, text, flags=re.IGNORECASE):
            # Avoid duplicate variations like React and React.js unless both appear
            if skill not in extracted:
                extracted.append(skill)

    return extracted


def parse_resume(file_path: str) -> Dict[str, Any]:
    """
    Main entry point: parses PDF or DOCX resume into structured profile with evidence.
    """
    text = extract_text(file_path)
    contact = extract_contact_information(text)
    academic = extract_academic_information(text)
    experience = extract_experience(text)
    skills = extract_skills(text)

    # Compile evidence records
    evidence = []
    
    if academic["cgpa"]["value"] is not None:
        evidence.append({
            "field_name": "cgpa_10",
            "value": str(academic["cgpa"]["value"]),
            "confidence": academic["cgpa"]["confidence"],
            "source_text": academic["cgpa"]["source_text"],
            "human_verified": False
        })

    if academic["tenth"]["value"] is not None:
        evidence.append({
            "field_name": "tenth_pct",
            "value": str(academic["tenth"]["value"]),
            "confidence": academic["tenth"]["confidence"],
            "source_text": academic["tenth"]["source_text"],
            "human_verified": False
        })

    if academic["twelfth"]["value"] is not None:
        evidence.append({
            "field_name": "twelfth_pct",
            "value": str(academic["twelfth"]["value"]),
            "confidence": academic["twelfth"]["confidence"],
            "source_text": academic["twelfth"]["source_text"],
            "human_verified": False
        })

    if academic["degree"]:
        evidence.append({
            "field_name": "degree",
            "value": academic["degree"],
            "confidence": "high",
            "source_text": academic["degree"],
            "human_verified": False
        })

    if academic["college"]:
        evidence.append({
            "field_name": "college",
            "value": academic["college"],
            "confidence": "high",
            "source_text": academic["college"],
            "human_verified": False
        })

    return {
        "name": contact["name"],
        "email": contact["email"],
        "phone": contact["phone"],
        "location": contact["location"],
        "college": academic["college"],
        "degree": academic["degree"],
        "grad_year": academic["grad_year"],
        "tenth_pct": academic["tenth"]["value"],
        "twelfth_pct": academic["twelfth"]["value"],
        "cgpa_10": academic["cgpa"]["value"],
        "years_experience": experience,
        "skills": skills,
        "resume_text": text,
        "evidence": evidence
    }
