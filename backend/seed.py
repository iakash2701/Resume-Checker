import os
import json
import glob
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models import Candidate, JobDescription, CandidateFieldEvidence, ConfidenceLevel
from app.services.resume_parser import parse_resume
import app.models

def seed_database():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        resumes_dir = os.path.join(base_dir, "data", "resumes")
        jds_dir = os.path.join(base_dir, "data", "jds")

        # 1. Seed JDs
        jd_files = glob.glob(os.path.join(jds_dir, "*.json"))
        print(f"Found {len(jd_files)} Job Descriptions...")
        for jd_file in jd_files:
            with open(jd_file, "r", encoding="utf-8") as f:
                jd_data = json.load(f)
            
            existing_jd = db.query(JobDescription).filter(JobDescription.title == jd_data["title"]).first()
            skills_str = ", ".join(jd_data.get("required_skills", [])) if isinstance(jd_data.get("required_skills"), list) else jd_data.get("required_skills", "")
            
            if not existing_jd:
                jd = JobDescription(
                    title=jd_data["title"],
                    description=jd_data["description"],
                    min_experience=float(jd_data.get("min_experience", 0.0)),
                    required_skills=skills_str
                )
                db.add(jd)
                print(f"  + Added JD: {jd_data['title']}")
            else:
                existing_jd.description = jd_data["description"]
                existing_jd.min_experience = float(jd_data.get("min_experience", 0.0))
                existing_jd.required_skills = skills_str
                print(f"  * Updated JD: {jd_data['title']}")

        db.commit()

        # 2. Parse and seed candidates from resume files using resume_parser
        resume_files = sorted(glob.glob(os.path.join(resumes_dir, "*.*")))
        print(f"Found {len(resume_files)} resume files in {resumes_dir}...")

        for file_path in resume_files:
            filename = os.path.basename(file_path)
            parsed = parse_resume(file_path)

            cand = db.query(Candidate).filter(Candidate.resume_filename == filename).first()
            if not cand:
                cand = Candidate(
                    name=parsed["name"] or "Candidate",
                    email=parsed["email"],
                    phone=parsed["phone"],
                    location=parsed["location"],
                    college=parsed["college"],
                    degree=parsed["degree"],
                    grad_year=parsed["grad_year"],
                    tenth_pct=parsed["tenth_pct"],
                    twelfth_pct=parsed["twelfth_pct"],
                    cgpa_10=parsed["cgpa_10"],
                    years_experience=parsed["years_experience"],
                    resume_filename=filename,
                    resume_text=parsed["resume_text"],
                    pipeline_stage="Applied"
                )
                db.add(cand)
                db.flush()
                print(f"  + Added Candidate: {cand.name} ({filename})")
            else:
                cand.name = parsed["name"] or cand.name
                cand.email = parsed["email"]
                cand.phone = parsed["phone"]
                cand.location = parsed["location"]
                cand.college = parsed["college"]
                cand.degree = parsed["degree"]
                cand.grad_year = parsed["grad_year"]
                cand.tenth_pct = parsed["tenth_pct"]
                cand.twelfth_pct = parsed["twelfth_pct"]
                cand.cgpa_10 = parsed["cgpa_10"]
                cand.years_experience = parsed["years_experience"]
                cand.resume_text = parsed["resume_text"]
                print(f"  * Updated Candidate: {cand.name} ({filename})")

            # Refresh evidence records for this candidate
            db.query(CandidateFieldEvidence).filter(CandidateFieldEvidence.candidate_id == cand.id).delete()

            for ev in parsed.get("evidence", []):
                db.add(CandidateFieldEvidence(
                    candidate_id=cand.id,
                    field_name=ev["field_name"],
                    value=ev["value"],
                    confidence=ev["confidence"],
                    source_text=ev["source_text"],
                    human_verified=ev.get("human_verified", False)
                ))

        db.commit()
        print("Database seeded with parsed resumes successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
