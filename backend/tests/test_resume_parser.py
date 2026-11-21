import pytest
from app.services.resume_parser import (
    extract_academic_information,
    extract_experience,
    extract_contact_information,
    extract_skills
)

def test_percentage_normalization():
    # 10th percentage variants
    samples_10 = [
        ("10th: 82%", 82.0),
        ("Xth Percentage: 82.5%", 82.5),
        ("SSC: 81%", 81.0),
        ("Matriculation - 78.4%", 78.4),
        ("Class X: 88%", 88.0),
        ("10th Standard: 85.5 %", 85.5),
        ("Secondary School Certificate: 90%", 90.0),
    ]
    for text, expected in samples_10:
        info = extract_academic_information(text)
        assert info["tenth"]["value"] == expected, f"Failed for {text}: got {info['tenth']['value']}"
        assert info["tenth"]["confidence"] in ["high", "medium"]

    # 12th percentage variants
    samples_12 = [
        ("12th: 78%", 78.0),
        ("XII Percentage: 81.5%", 81.5),
        ("HSC: 76%", 76.0),
        ("Intermediate - 84%", 84.0),
        ("Class XII: 82.5%", 82.5),
        ("Higher Secondary: 80%", 80.0),
    ]
    for text, expected in samples_12:
        info = extract_academic_information(text)
        assert info["twelfth"]["value"] == expected, f"Failed for {text}: got {info['twelfth']['value']}"
        assert info["twelfth"]["confidence"] in ["high", "medium"]

def test_cgpa_normalization_10_scale():
    samples_10_scale = [
        ("CGPA: 8.2", 8.2),
        ("CGPA 8.2/10", 8.2),
        ("8.2 / 10", 8.2),
        ("CGPA - 7.9", 7.9),
        ("Overall Academic Score: 7.68 CGPA", 7.68),
    ]
    for text, expected in samples_10_scale:
        info = extract_academic_information(text)
        assert abs(info["cgpa"]["value"] - expected) <= 0.05, f"Failed for {text}: got {info['cgpa']['value']}"
        assert info["cgpa"]["confidence"] in ["high", "medium"]

def test_cgpa_normalization_4_scale():
    samples_4_scale = [
        ("GPA: 3.4/4.0", 8.5),       # 3.4 / 4 * 10 = 8.5
        ("3.4 / 4.0", 8.5),
        ("CGPA (4-pt scale): 3.2/4.0", 8.0), # 3.2 / 4 * 10 = 8.0
        ("Grade Point Average: 3.85 on a 4.0 scale", 9.62), # 3.85 / 4 * 10 = 9.625 -> 9.62
    ]
    for text, expected in samples_4_scale:
        info = extract_academic_information(text)
        assert abs(info["cgpa"]["value"] - expected) <= 0.05, f"Failed for {text}: got {info['cgpa']['value']}"
        assert info["cgpa"]["confidence"] == "high"

def test_experience_extraction():
    samples_exp = [
        ("Fresher", 0.0),
        ("Status: Fresher looking for opportunities", 0.0),
        ("6 months internship experience", 0.5),
        ("Worked for 18 months", 1.5),
        ("Experience: 1 year", 1.0),
        ("1.5 years experience", 1.5),
        ("2 years of professional experience", 2.0),
        ("Over 3.0 years in software engineering", 3.0),
    ]
    for text, expected in samples_exp:
        exp = extract_experience(text)
        assert abs(exp - expected) <= 0.05, f"Failed for {text}: got {exp}"

def test_missing_fields_remain_none():
    text = "Rahul Kumar\nB.Tech Computer Science\nFresher"
    info = extract_academic_information(text)
    assert info["tenth"]["value"] is None
    assert info["twelfth"]["value"] is None
    assert info["cgpa"]["value"] is None
    assert info["tenth"]["confidence"] == "low"
    assert info["cgpa"]["confidence"] == "low"

def test_graduation_year_extraction():
    samples_grad = [
        ("B.Tech (Graduation: 2028)", 2028),
        ("Class of 2026", 2026),
        ("Graduating in 2027", 2027),
        ("2024-2028", 2028),
    ]
    for text, expected in samples_grad:
        info = extract_academic_information(text)
        assert info["grad_year"] == expected, f"Failed for {text}: got {info['grad_year']}"

def test_skills_extraction():
    text = "Proficiencies: Python, FastAPI, React, PostgreSQL, Docker, Git"
    skills = extract_skills(text)
    assert "Python" in skills
    assert "FastAPI" in skills
    assert "React" in skills
    assert "PostgreSQL" in skills
    assert "Docker" in skills
    assert "Git" in skills
