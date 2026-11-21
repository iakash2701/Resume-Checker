import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

# 1. Candidate Search across name, college, degree, location, skills
def test_candidate_search_by_name(client):
    res = client.get("/api/candidates?search=Rahul")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    for cand in data["items"]:
        assert "Rahul" in cand["name"]

def test_candidate_search_by_college(client):
    res = client.get("/api/candidates?search=PSG")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    for cand in data["items"]:
        assert "PSG" in (cand["college"] or "")

def test_candidate_search_by_location(client):
    res = client.get("/api/candidates?search=Bengaluru")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    for cand in data["items"]:
        assert "Bengaluru" in (cand["location"] or "") or "Bengaluru" in (cand["resume_text"] or "")

def test_candidate_search_combined_with_filters(client):
    res = client.get("/api/candidates?search=Rahul&cgpa_min=7.0&skills=Python")
    assert res.status_code == 200
    data = res.json()
    for cand in data["items"]:
        assert "Rahul" in cand["name"]
        assert cand["cgpa_10"] >= 7.0

# 2. Candidate Editing and Validation
def test_candidate_edit_academic_and_location(client):
    payload = {
        "cgpa_10": 8.75,
        "tenth_pct": 89.2,
        "twelfth_pct": 87.4,
        "location": "Chennai, Tamil Nadu",
        "years_experience": 2.5
    }
    res = client.patch("/api/candidates/1", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["cgpa_10"] == 8.75
    assert data["tenth_pct"] == 89.2
    assert data["twelfth_pct"] == 87.4
    assert data["location"] == "Chennai, Tamil Nadu"
    assert data["years_experience"] == 2.5

def test_candidate_edit_validation_invalid_cgpa(client):
    payload = {"cgpa_10": 11.5}  # Above max 10.0
    res = client.patch("/api/candidates/1", json=payload)
    assert res.status_code == 422

def test_candidate_edit_validation_negative_experience(client):
    payload = {"years_experience": -1.0}
    res = client.patch("/api/candidates/1", json=payload)
    assert res.status_code == 422

# 3. Pipeline Stage Transition and Validation
def test_candidate_stage_transition(client):
    # Transition candidate 1 to Shortlisted
    res = client.patch("/api/candidates/1/stage", json={"stage": "Shortlisted"})
    assert res.status_code == 200
    assert res.json()["pipeline_stage"] == "Shortlisted"

    # Move to Interview
    res = client.patch("/api/candidates/1/stage", json={"stage": "Interview"})
    assert res.status_code == 200
    assert res.json()["pipeline_stage"] == "Interview"

def test_candidate_stage_transition_invalid_stage(client):
    res = client.patch("/api/candidates/1/stage", json={"stage": "HiredPermanently"})
    assert res.status_code == 400
    assert "Invalid stage" in res.json()["detail"]

# 4. Audit Log Creation and Retrieval
def test_candidate_audit_history(client):
    res = client.get("/api/candidates/1/audit")
    assert res.status_code == 200
    logs = res.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    # Latest log should reflect the stage move
    assert logs[0]["to_stage"] in ["Shortlisted", "Interview"]
    assert "changed_by" in logs[0]
    assert "changed_at" in logs[0]

# 5. Evidence Verification & Preserving Source
def test_verify_evidence_confirm(client):
    payload = {
        "field_name": "cgpa_10",
        "value": "8.75",
        "confirmed": True
    }
    res = client.post("/api/candidates/1/verify-evidence", json=payload)
    assert res.status_code == 200
    cand = res.json()
    ev_list = cand["evidence_fields"]
    cgpa_ev = next((ev for ev in ev_list if ev["field_name"] == "cgpa_10"), None)
    assert cgpa_ev is not None
    assert cgpa_ev["confidence"] == "verified"
    assert cgpa_ev["human_verified"] is True
    # Verify source text is preserved
    assert cgpa_ev["source_text"] is not None

# 6. Review Queue Endpoint
def test_review_queue_retrieval(client):
    res = client.get("/api/candidates/review-queue")
    assert res.status_code == 200
    queue = res.json()
    assert isinstance(queue, list)
    assert len(queue) > 0
    # Candidates with missing academic fields (candidate 10, 11, 12) must be in the queue
    queue_filenames = [c["resume_filename"] for c in queue]
    assert "resume_010.pdf" in queue_filenames  # missing 10th
    assert "resume_011.pdf" in queue_filenames  # missing CGPA
    assert "resume_012.pdf" in queue_filenames  # missing grad year

# 7. Stats endpoint comprehensive review counts
def test_stats_comprehensive_metrics(client):
    res = client.get("/api/stats")
    assert res.status_code == 200
    stats = res.json()
    assert "average_jd_match" in stats
    assert "candidates_with_confidence_issues" in stats
    assert "candidates_requiring_review" in stats
    assert "fields_needing_verification" in stats
    assert stats["candidates_requiring_review"] > 0
