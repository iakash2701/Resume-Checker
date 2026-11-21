import time
import random
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Candidate

def run_perf_benchmark():
    db = SessionLocal()
    print("Preparing 500 candidates for performance test...")
    try:
        # Check current count
        current_count = db.query(Candidate).count()
        needed = 500 - current_count
        
        sample_skills = [
            ["Python", "FastAPI", "Docker", "Git"],
            ["React", "Node.js", "JavaScript", "TypeScript"],
            ["Java", "Spring Boot", "MySQL", "AWS"],
            ["Python", "Machine Learning", "SQL", "Pandas"],
            ["DevOps", "Kubernetes", "Linux", "Docker", "CI/CD"],
            ["Power BI", "SQL", "Excel", "Tableau", "Data Analysis"]
        ]
        colleges = ["IIT Madras", "BITS Pilani", "PSG Tech", "VIT", "NIT Trichy"]
        degrees = ["B.Tech Computer Science", "B.E. Information Technology", "MCA", "B.Tech AI & ML"]
        locations = ["Bengaluru", "Chennai", "Hyderabad", "Pune", "Mumbai", "Delhi"]

        if needed > 0:
            print(f"Generating {needed} benchmark candidates...")
            for i in range(1, needed + 1):
                idx = current_count + i
                skills = random.choice(sample_skills)
                c = Candidate(
                    name=f"Benchmark Candidate {idx}",
                    email=f"candidate_{idx}@benchmark.org",
                    phone=f"9{random.randint(100000000, 999999999)}",
                    location=random.choice(locations),
                    college=random.choice(colleges),
                    degree=random.choice(degrees),
                    grad_year=random.choice([2023, 2024, 2025, 2026]),
                    tenth_pct=round(random.uniform(60.0, 98.0), 1),
                    twelfth_pct=round(random.uniform(60.0, 98.0), 1),
                    cgpa_10=round(random.uniform(6.0, 9.9), 2),
                    years_experience=round(random.uniform(0.0, 6.0), 1),
                    resume_filename=f"bench_resume_{idx}.pdf",
                    resume_text=f"Benchmark profile for Candidate {idx}.\nSkills: {', '.join(skills)}\nEducation: {random.choice(degrees)}",
                    pipeline_stage="Applied"
                )
                db.add(c)
            db.commit()
            print("Successfully populated 500 candidates in SQLite database.")
        else:
            print(f"Database already has {current_count} candidates.")

        client = TestClient(app)

        test_queries = [
            ("Unfiltered paginated query", "/api/candidates?page=1&page_size=50"),
            ("Academic SQL range filter (10th >= 75, CGPA >= 8.0)", "/api/candidates?tenth_min=75&cgpa_min=8.0&page_size=50"),
            ("Skill synonym filter (React via 'reactjs')", "/api/candidates?skills=reactjs&page_size=50"),
            ("Multi-skill AND filter (Python, Docker)", "/api/candidates?skills=Python,Docker&skills_mode=and&page_size=50"),
            ("Complex combined filter (Exp: 1-3 yrs, Grad: 2025, CGPA >= 7.5, Location: Bengaluru)", "/api/candidates?exp_min=1.0&exp_max=3.0&grad_year=2025&cgpa_min=7.5&location=Bengaluru&page_size=50"),
            ("Full JD matching with 4-part score breakdown (JD #1)", "/api/candidates?jd_id=1&sort=match_desc&page_size=50")
        ]

        print("\n" + "=" * 65)
        print("HIRESWIFT 500-CANDIDATE PERFORMANCE BENCHMARK")
        print("=" * 65)
        for label, url in test_queries:
            times = []
            for _ in range(5):
                start = time.perf_counter()
                res = client.get(url)
                end = time.perf_counter()
                assert res.status_code == 200
                times.append((end - start) * 1000)
            avg_time = sum(times) / len(times)
            min_time = min(times)
            print(f"{label:<50} | Avg: {avg_time:>6.2f} ms (Min: {min_time:>6.2f} ms)")
        print("=" * 65 + "\n")

    finally:
        db.close()

if __name__ == "__main__":
    run_perf_benchmark()
