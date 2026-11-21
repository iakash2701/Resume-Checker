import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

# 1. No filters applied: all candidates pass
def test_whatif_no_filters(client):
    payload = {}
    res = client.post("/api/whatif", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_candidates"] > 0
    assert data["passing_candidates"] == data["total_candidates"]
    assert data["removed_candidates"] == 0
    assert len(data["filters"]) == 0

# 2. Single filter: 10th percentage
def test_whatif_single_filter(client):
    payload = {"tenth_pct": 80.0}
    res = client.post("/api/whatif", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["filters"]) == 1
    f = data["filters"][0]
    assert "10th" in f["filter"]
    assert f["before"] == data["total_candidates"]
    assert f["after"] <= f["before"]
    assert f["removed"] == f["before"] - f["after"]
    assert f["percentage_removed"] >= 0.0

# 3. Sequential multi-filter funnel
def test_whatif_sequential_funnel(client):
    payload = {
        "tenth_pct": 70.0,
        "twelfth_pct": 70.0,
        "cgpa": 7.5,
        "years_experience": 1.0
    }
    res = client.post("/api/whatif", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["filters"]) == 4
    # Ensure sequential chaining: before of stage i+1 == after of stage i
    for i in range(len(data["filters"]) - 1):
        assert data["filters"][i]["after"] == data["filters"][i+1]["before"]
    assert data["passing_candidates"] == data["filters"][-1]["after"]
    assert data["removed_candidates"] == data["total_candidates"] - data["passing_candidates"]

# 4. AND skills vs OR skills in What-If
def test_whatif_skills_and_vs_or(client):
    payload_and = {
        "skills": ["Python", "Docker"],
        "skill_mode": "AND"
    }
    payload_or = {
        "skills": ["Python", "Docker"],
        "skill_mode": "OR"
    }
    res_and = client.post("/api/whatif", json=payload_and)
    res_or = client.post("/api/whatif", json=payload_or)
    assert res_and.status_code == 200
    assert res_or.status_code == 200
    assert res_or.json()["passing_candidates"] >= res_and.json()["passing_candidates"]

# 5. Near-miss candidates detection
def test_whatif_near_miss_detection(client):
    # Set high CGPA threshold so some candidates miss by <= 0.5
    payload = {"cgpa": 8.5}
    res = client.post("/api/whatif", json=payload)
    assert res.status_code == 200
    data = res.json()
    near_misses = data["near_miss_candidates"]
    assert isinstance(near_misses, list)
    if near_misses:
        first = near_misses[0]
        assert "candidate_id" in first
        assert "name" in first
        assert "failed_filter" in first
        assert "gap" in first
        assert first["gap"] <= 0.5
        assert first["gap"] > 0

# 6. High-match candidate exclusions with JD
def test_whatif_high_match_exclusions(client):
    # Select JD #1 (Full Stack) and set strict academic filters
    payload = {
        "jd_id": 1,
        "cgpa": 9.5,  # Very strict
        "years_experience": 4.0
    }
    res = client.post("/api/whatif", json=payload)
    assert res.status_code == 200
    data = res.json()
    high_match = data["high_match_removed"]
    assert isinstance(high_match, list)
    # Excluded candidates with match_score >= 75 should be flagged
    for cand in high_match:
        assert cand["match_score"] >= 75.0
        assert len(cand["failed_filters"]) > 0

# 7. Relaxation suggestions calculation
def test_whatif_relaxation_suggestions(client):
    payload = {
        "cgpa": 8.5,
        "tenth_pct": 85.0,
        "years_experience": 2.0
    }
    res = client.post("/api/whatif", json=payload)
    assert res.status_code == 200
    data = res.json()
    suggestions = data["relaxation_suggestions"]
    assert isinstance(suggestions, list)
    for s in suggestions:
        assert "filter_name" in s
        assert "current_value" in s
        assert "suggested_value" in s
        assert "recovered_count" in s
        assert s["recovered_count"] > 0
        assert s["suggested_value"] < s["current_value"]

# 8. Location and Grad Year filters in What-If
def test_whatif_location_and_grad_year(client):
    payload = {
        "location": "Bengaluru",
        "grad_year": 2025
    }
    res = client.post("/api/whatif", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["filters"]) == 2
