import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Candidate, JobDescription, AuditLog
from app.services.email_service import process_bulk_email_queue, EMAIL_TEMPLATES
from app.services.dedup_service import compute_candidate_similarity, find_duplicates_for_candidate
from app.services.intelligence_service import analyze_skill_gap, analyze_hiring_intelligence

@pytest.fixture
def client():
    return TestClient(app)

# ----------------- 1. DUPLICATE RESUME DETECTION TESTS -----------------

def test_exact_duplicate_detection():
    c1 = Candidate(
        name="Rahul Kumar",
        email="rahul.kumar@gmail.com",
        phone="9876543210",
        college="IIT Madras",
        grad_year=2024,
        years_experience=2.0,
        resume_text="Experienced Python and SQL developer at Tech Corp with FastAPI and Docker skills."
    )
    c2 = Candidate(
        name="Rahul Kumar",
        email="rahul.kumar@gmail.com",
        phone="9876543210",
        college="IIT Madras",
        grad_year=2024,
        years_experience=2.0,
        resume_text="Experienced Python and SQL developer at Tech Corp with FastAPI and Docker skills."
    )
    res = compute_candidate_similarity(c1, c2)
    assert res["similarity_score"] >= 95.0
    assert res["classification"] == "EXACT DUPLICATE"
    assert any("email" in r.lower() for r in res["reasons"])

def test_likely_duplicate_detection():
    c1 = Candidate(
        name="Ananya Sharma",
        email="ananya.sharma@gmail.com",
        phone="9123456780",
        college="BITS Pilani",
        grad_year=2025,
        years_experience=1.5,
        resume_text="Frontend engineer specialized in React, TypeScript, Tailwind CSS with Redux project."
    )
    c2 = Candidate(
        name="Ananya S",
        email="ananya.sharma2025@outlook.com",
        phone="9123456780", # same phone
        college="BITS Pilani",
        grad_year=2025,
        years_experience=1.5,
        resume_text="Frontend engineer specialized in React, TypeScript, Tailwind CSS with Redux portfolio."
    )
    res = compute_candidate_similarity(c1, c2)
    assert res["similarity_score"] >= 80.0
    assert res["classification"] in ["EXACT DUPLICATE", "LIKELY DUPLICATE"]

def test_unique_candidate_detection():
    c1 = Candidate(
        name="Priya Patel",
        email="priya.p@gmail.com",
        phone="9988776655",
        college="NIT Trichy",
        grad_year=2023,
        years_experience=3.0,
        resume_text="DevOps engineer working with Kubernetes, Terraform, AWS, and CI/CD pipelines."
    )
    c2 = Candidate(
        name="Vikram Singh",
        email="vikram.s@yahoo.com",
        phone="9112233445",
        college="Anna University",
        grad_year=2026,
        years_experience=0.5,
        resume_text="Junior Data Analyst with skills in Excel, Power BI, and Tableau."
    )
    res = compute_candidate_similarity(c1, c2)
    assert res["similarity_score"] < 60.0
    assert res["classification"] == "UNIQUE"

def test_duplicate_review_and_marking(client):
    # Verify duplicates endpoint works on candidate 1
    res = client.get("/api/candidates/1/duplicates?threshold=40")
    assert res.status_code == 200
    data = res.json()
    assert "has_duplicates" in data
    assert "matches" in data

    # Test marking as duplicate
    mark_res = client.post("/api/candidates/2/mark-duplicate", json={"duplicate_of_id": 1})
    assert mark_res.status_code == 200
    assert mark_res.json()["status"] == "ok"

    # Verify candidate 2 was marked as duplicate and pipeline_stage is Rejected without deleting
    chk = client.get("/api/candidates/2")
    assert chk.status_code == 200
    assert chk.json()["pipeline_stage"] == "Rejected"

    # Verify audit log recorded duplicate mark
    audit_res = client.get("/api/candidates/2/audit")
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert any("duplicate of Candidate #1" in log["changed_by"] for log in logs)


# ----------------- 2. SKILL-GAP INSIGHTS TESTS -----------------

def test_skill_gap_analysis(client):
    # Fetch candidate 1 and JD 1
    res = client.get("/api/candidates/1/skill-gap?jd_id=1")
    assert res.status_code == 200
    data = res.json()
    assert "total_required" in data
    assert "matched_required" in data
    assert "missing_required" in data
    assert "skill_coverage_pct" in data
    assert isinstance(data["skill_coverage_pct"], float)
    assert 0 <= data["skill_coverage_pct"] <= 100

def test_skill_gap_all_skills_matched():
    c = Candidate(
        name="Test Dev",
        resume_text="Senior engineer with deep expertise in Python, FastAPI, Docker, and PostgreSQL."
    )
    jd = JobDescription(
        title="Python Dev",
        description="We need Python and FastAPI",
        required_skills="Python, FastAPI",
        nice_to_have_skills="Docker"
    )
    res = analyze_skill_gap(c, jd)
    assert len(res["missing_required"]) == 0
    assert res["skill_coverage_pct"] == 100.0
    assert "Python" in res["matched_required"]
    assert "FastAPI" in res["matched_required"]

def test_skill_gap_no_skills_matched():
    c = Candidate(
        name="Test Designer",
        resume_text="Graphic designer skilled in Photoshop, Figma, Illustrator."
    )
    jd = JobDescription(
        title="Backend Dev",
        description="We need Rust and Go",
        required_skills="Python, SQL",
        nice_to_have_skills=""
    )
    res = analyze_skill_gap(c, jd)
    assert len(res["matched_required"]) == 0
    assert res["skill_coverage_pct"] == 0.0
    assert "Python" in res["missing_required"]
    assert "SQL" in res["missing_required"]


# ----------------- 3. EVIDENCE INTELLIGENCE & INTERVIEW PROBES TESTS -----------------

def test_evidence_strength_and_probes(client):
    res = client.get("/api/candidates/1/intelligence?jd_id=1")
    assert res.status_code == 200
    intel = res.json()
    assert "evidence_score" in intel
    assert 0 <= intel["evidence_score"] <= 100
    assert "evidence_items" in intel
    assert len(intel["evidence_items"]) > 0
    assert "evidence_graph" in intel

    # Check probe format
    first_item = intel["evidence_items"][0]
    assert "interview_probe" in first_item
    assert len(first_item["interview_probe"]) > 10
    assert first_item["confidence"] in ["HIGH", "MEDIUM", "LOW"]

def test_weak_claim_vs_project_evidence():
    c = Candidate(
        name="Claim Test",
        resume_text="""
Skills: Docker, Kubernetes, AWS

Projects:
Automated Machine Learning Pipeline
Developed a comprehensive Python prediction engine with SQL database querying and FastAPI endpoint servicing.
"""
    )
    intel = analyze_hiring_intelligence(c)
    items_by_skill = {item["skill"].lower(): item for item in intel["evidence_items"]}

    # Python should have high confidence / strong evidence from Projects section
    if "python" in items_by_skill:
        assert items_by_skill["python"]["confidence"] == "HIGH"
        assert items_by_skill["python"]["source_type"] == "Project Experience"

    # Docker was only in skills list
    if "docker" in items_by_skill:
        assert items_by_skill["docker"]["confidence"] in ["LOW", "MEDIUM"]
        assert "Docker" in items_by_skill["docker"]["interview_probe"]


# ----------------- 4. BULK EMAIL SMTP DRY-RUN TESTS -----------------

def test_bulk_email_dry_run():
    candidates = [
        {"id": 101, "name": "Arjun Sharma", "email": "arjun@example.com", "skills": "Python, FastAPI"},
        {"id": 102, "name": "Neha Gupta", "email": "neha@test.org", "skills": "React, Tailwind"}
    ]
    res = process_bulk_email_queue(
        items=candidates,
        template_key="interview_invitation",
        role="Full Stack Engineer",
        dry_run=True
    )
    assert res["mode"] == "DRY RUN"
    assert res["total_queued"] == 2
    assert res["total_delivered"] == 0
    for q in res["queue"]:
        assert q["dry_run"] is True
        assert "DRY RUN" in q["status"]
        assert "Full Stack Engineer" in q["subject"]
        assert "Dear" in q["body"]

def test_bulk_email_invalid_recipient():
    candidates = [
        {"id": 103, "name": "No Email User", "email": "invalid-email-format", "skills": "SQL"}
    ]
    res = process_bulk_email_queue(
        items=candidates,
        template_key="shortlist_notification",
        dry_run=True
    )
    assert res["queue"][0]["status"] == "Invalid recipient email address"

def test_bulk_email_missing_smtp_blocks_live():
    candidates = [
        {"id": 104, "name": "Pooja Roy", "email": "pooja@example.com", "skills": "Java"}
    ]
    # Requesting live dispatch without SMTP configuration must safely fall back to dry run
    res = process_bulk_email_queue(
        items=candidates,
        template_key="application_update",
        dry_run=False,
        smtp_host=None
    )
    assert res["mode"] == "DRY RUN"
    assert "SMTP not configured" in res["queue"][0]["status"]
    assert res["total_delivered"] == 0

def test_bulk_email_api_endpoint(client):
    payload = {
        "candidates": [
            {"id": 1, "name": "Candidate One", "email": "one@example.com", "skills": "Python"}
        ],
        "template_key": "interview_invitation",
        "role": "Backend Lead",
        "dry_run": True
    }
    res = client.post("/api/email/bulk", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "DRY RUN"
    assert len(data["queue"]) == 1
    assert "Backend Lead" in data["queue"][0]["subject"]
