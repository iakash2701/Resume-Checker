import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Candidate, JobDescription

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_seeded_data_exists():
    db = SessionLocal()
    try:
        candidate_count = db.query(Candidate).count()
        jd_count = db.query(JobDescription).count()
        assert candidate_count == 40, f"Expected 40 candidates, found {candidate_count}"
        assert jd_count >= 3, f"Expected at least 3 JDs, found {jd_count}"
    finally:
        db.close()

def test_get_candidates_api(client):
    response = client.get("/api/candidates")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 40
    assert len(data["items"]) > 0
    first = data["items"][0]
    assert "name" in first
    assert "email" in first
    assert "cgpa_10" in first
    assert "pipeline_stage" in first

def test_get_candidate_by_id(client):
    response = client.get("/api/candidates/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "name" in data
    assert "evidence_fields" in data
    assert len(data["evidence_fields"]) > 0

def test_get_candidate_not_found(client):
    response = client.get("/api/candidates/99999")
    assert response.status_code == 404

def test_get_jds_api(client):
    response = client.get("/api/jds")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    titles = [jd["title"] for jd in data]
    assert "Full-Stack Developer" in titles
    assert "Data Analyst" in titles
    assert "DevOps Engineer" in titles

def test_stats_api(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_candidates"] == 40
    assert stats["applied"] >= 0
    assert (stats["applied"] + stats["shortlisted"] + stats["interview"] + stats["offers"] + stats["rejected"]) == stats["total_candidates"]
    assert stats["total_jds"] >= 3
