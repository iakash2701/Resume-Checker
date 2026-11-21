import pytest
import json
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

# --- 1. CANDIDATE COMPARISON TESTS ---
def test_compare_two_candidates(client):
    payload = {"candidate_ids": [1, 2], "jd_id": 1}
    res = client.post("/api/candidates/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["candidates"]) == 2
    assert "radar_data" in data
    assert len(data["radar_data"]) == 4  # Skills, Experience, Education, JD Match
    assert "verdict" in data
    assert len(data["verdict"]) > 0

def test_compare_three_candidates(client):
    payload = {"candidate_ids": [1, 2, 3], "jd_id": 1}
    res = client.post("/api/candidates/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["candidates"]) == 3
    assert len(data["radar_data"][0]) >= 4  # dimension + 3 candidate names

def test_compare_less_than_two_rejected(client):
    payload = {"candidate_ids": [1], "jd_id": 1}
    res = client.post("/api/candidates/compare", json=payload)
    assert res.status_code == 400
    assert "requires exactly 2 or 3 candidates" in res.json()["detail"]

def test_compare_more_than_three_rejected(client):
    payload = {"candidate_ids": [1, 2, 3, 4], "jd_id": 1}
    res = client.post("/api/candidates/compare", json=payload)
    assert res.status_code == 400
    assert "requires exactly 2 or 3 candidates" in res.json()["detail"]

def test_compare_verdict_and_radar_dimensions(client):
    payload = {"candidate_ids": [1, 4], "jd_id": 1}
    res = client.post("/api/candidates/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    for card in data["candidates"]:
        assert "normalized_scores" in card
        for dim in ["Skills", "Experience", "Education", "JD Match"]:
            score = card["normalized_scores"][dim]
            assert 0.0 <= score <= 100.0
    assert "shared_skills" in data

# --- 2. CSV EXPORT & SECURITY TESTS ---
def test_export_candidates_csv_basic(client):
    res = client.get("/api/candidates/export")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    lines = res.text.strip().split("\r\n") if "\r\n" in res.text else res.text.strip().split("\n")
    assert len(lines) >= 41  # Header + 40 records
    header = lines[0]
    assert "Candidate Name" in header
    assert "JD Match Score" in header
    assert "CGPA" in header

def test_export_candidates_csv_filtered(client):
    res = client.get("/api/candidates/export?cgpa_min=8.5")
    assert res.status_code == 200
    lines = res.text.strip().split("\r\n") if "\r\n" in res.text else res.text.strip().split("\n")
    # Header + filtered records
    assert len(lines) > 1
    assert len(lines) < 41

def test_export_csv_formula_injection_sanitization():
    from app.services.export_service import sanitize_csv_cell
    assert sanitize_csv_cell("=cmd|'/C calc'!A0") == "'=cmd|'/C calc'!A0"
    assert sanitize_csv_cell("+12345") == "'+12345"
    assert sanitize_csv_cell("-50") == "'-50"
    assert sanitize_csv_cell("@SUM(1,2)") == "'@SUM(1,2)"
    assert sanitize_csv_cell("Rahul Kumar") == "Rahul Kumar"
    assert sanitize_csv_cell(None) == ""

# --- 3. FILTER PRESETS TESTS ---
def test_preset_lifecycle(client):
    preset_data = {
        "name": "Phase 6 Test Preset - Full Stack",
        "filters_json": json.dumps({
            "cgpa": 7.5,
            "tenth_pct": 70,
            "skills": ["React", "Node.js"],
            "skill_mode": "AND",
            "years_experience": 1.0
        })
    }
    # 1. Create
    res_create = client.post("/api/presets", json=preset_data)
    assert res_create.status_code == 200
    created = res_create.json()
    preset_id = created["id"]
    assert created["name"] == preset_data["name"]

    # 2. Get list
    res_list = client.get("/api/presets")
    assert res_list.status_code == 200
    names = [p["name"] for p in res_list.json()]
    assert preset_data["name"] in names

    # 3. Duplicate name rejection
    res_dup = client.post("/api/presets", json=preset_data)
    assert res_dup.status_code == 400
    assert "already exists" in res_dup.json()["detail"]

    # 4. Update
    update_data = {"name": "Phase 6 Updated Preset Name"}
    res_up = client.put(f"/api/presets/{preset_id}", json=update_data)
    assert res_up.status_code == 200
    assert res_up.json()["name"] == "Phase 6 Updated Preset Name"

    # 5. Delete
    res_del = client.delete(f"/api/presets/{preset_id}")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "ok"

    # 6. Verify deleted
    res_list2 = client.get("/api/presets")
    names2 = [p["name"] for p in res_list2.json()]
    assert "Phase 6 Updated Preset Name" not in names2

def test_preset_validation_empty_name(client):
    res = client.post("/api/presets", json={"name": "   ", "filters_json": "{}"})
    assert res.status_code == 400

def test_preset_validation_invalid_json(client):
    res = client.post("/api/presets", json={"name": "Valid Name", "filters_json": "INVALID_NOT_JSON"})
    assert res.status_code == 400
