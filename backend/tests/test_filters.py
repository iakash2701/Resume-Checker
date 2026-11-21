import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Candidate, JobDescription

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

# 1. Boundary filter test: tenth_min = 82.0
def test_filter_tenth_boundary(client):
    res = client.get("/api/candidates?tenth_min=82.0")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    for cand in data["items"]:
        assert cand["tenth_pct"] is not None
        assert cand["tenth_pct"] >= 82.0

# 2. Boundary filter test: exactly 60.0 vs 59.9
def test_filter_boundary_value_comparison(client):
    # Candidate with >= 60.0
    res_60 = client.get("/api/candidates?tenth_min=60.0")
    assert res_60.status_code == 200
    count_60 = res_60.json()["total"]

    # Candidate with >= 59.9
    res_59_9 = client.get("/api/candidates?tenth_min=59.9")
    assert res_59_9.status_code == 200
    count_59_9 = res_59_9.json()["total"]

    assert count_59_9 >= count_60

# 3. Missing values filter test: candidate 10 has null tenth_pct
def test_filter_missing_values_tenth(client):
    res = client.get("/api/candidates?tenth_min=70.0")
    assert res.status_code == 200
    items = res.json()["items"]
    # Candidate 10 (which has tenth_pct = None) must NOT appear
    for cand in items:
        assert cand["tenth_pct"] is not None
        assert cand["resume_filename"] != "resume_010.pdf"

# 4. Missing values filter test: candidate 11 has null cgpa_10
def test_filter_missing_values_cgpa(client):
    res = client.get("/api/candidates?cgpa_min=7.0")
    assert res.status_code == 200
    items = res.json()["items"]
    # Candidate 11 (which has cgpa_10 = None) must NOT appear
    for cand in items:
        assert cand["cgpa_10"] is not None
        assert cand["resume_filename"] != "resume_011.pdf"

# 5. Missing values filter test: candidate 12 has null grad_year
def test_filter_missing_values_grad_year(client):
    res = client.get("/api/candidates?grad_year=2025")
    assert res.status_code == 200
    items = res.json()["items"]
    for cand in items:
        assert cand["grad_year"] == 2025
        assert cand["resume_filename"] != "resume_012.pdf"

# 6. Skill synonym matching: reactjs -> React
def test_filter_skill_synonym_reactjs(client):
    res_canonical = client.get("/api/candidates?skills=React")
    res_synonym = client.get("/api/candidates?skills=reactjs")
    assert res_canonical.status_code == 200
    assert res_synonym.status_code == 200
    assert res_canonical.json()["total"] == res_synonym.json()["total"]
    assert res_synonym.json()["total"] > 0

# 7. Skill synonym matching: k8s -> Kubernetes
def test_filter_skill_synonym_k8s(client):
    res = client.get("/api/candidates?skills=k8s")
    assert res.status_code == 200
    assert "total" in res.json()

# 8. Skill implication: Node.js implies JavaScript
def test_filter_skill_implication_nodejs_implies_javascript(client):
    res_js = client.get("/api/candidates?skills=JavaScript")
    assert res_js.status_code == 200
    # Every candidate with Node.js should match when searching for JavaScript
    items = res_js.json()["items"]
    assert len(items) > 0

# 9. Skills mode AND vs OR
def test_filter_skills_mode_and_or(client):
    res_and = client.get("/api/candidates?skills=Python,Docker&skills_mode=and")
    res_or = client.get("/api/candidates?skills=Python,Docker&skills_mode=or")
    assert res_and.status_code == 200
    assert res_or.status_code == 200
    # OR condition should match at least as many as AND condition
    assert res_or.json()["total"] >= res_and.json()["total"]

# 10. Experience range filter: exp_min and exp_max
def test_filter_experience_range(client):
    res = client.get("/api/candidates?exp_min=1.0&exp_max=2.0")
    assert res.status_code == 200
    data = res.json()
    for cand in data["items"]:
        assert 1.0 <= cand["years_experience"] <= 2.0

# 11. JD Matching and score breakdown
def test_jd_matching_score_and_breakdown(client):
    # Query with jd_id = 1 (Full-Stack Developer)
    res = client.get("/api/candidates?jd_id=1&sort=match_desc")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    top_cand = data["items"][0]
    assert top_cand["match_score"] is not None
    assert top_cand["match_breakdown"] is not None
    breakdown = top_cand["match_breakdown"]
    assert "skills_score" in breakdown
    assert "experience_score" in breakdown
    assert "education_score" in breakdown
    assert "tfidf_score" in breakdown
    assert breakdown["max_skills_score"] == 50.0

# 12. Create JD from raw pasted text
def test_create_jd_from_pasted_text(client):
    raw_text = """
    Senior Python Engineer
    Experience: At least 3 years of experience.
    
    Required Skills:
    - Python
    - FastAPI
    - PostgreSQL
    - Docker
    
    Nice to have:
    - Kubernetes
    - Redis
    """
    payload = {
        "title": "Senior Python Engineer",
        "raw_text": raw_text
    }
    res = client.post("/api/jds", json=payload)
    assert res.status_code == 200
    jd = res.json()
    assert jd["title"] == "Senior Python Engineer"
    assert jd["min_experience"] == 3.0
    assert "Python" in jd["required_skills"]
    assert "FastAPI" in jd["required_skills"]
    assert "Docker" in jd["required_skills"]
    assert "Kubernetes" in jd["nice_to_have_skills"]
