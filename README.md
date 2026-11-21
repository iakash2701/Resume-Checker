# HireSwift — Smart ATS for Small Teams

HireSwift is an Applicant Tracking System (ATS) engineered for small companies and high-velocity recruitment teams. It replaces generic parsing and opaque matching with **Indian academic normalization**, **TF-IDF + synonym skill matching**, **What-If Funnel optimization**, **evidence-based hiring intelligence**, and **safe bulk candidate outreach**.

---

## ⚡ Hackathon Quickstart (One-Click Demo Setup)

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Git

### 1. Backend Setup & Seed Data
```bash
# Navigate to backend
cd backend

# Create & activate virtual environment (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies (fastapi, rapidfuzz, uvicorn, sqlalchemy, etc.)
pip install -r requirements.txt

# Run database setup & synthetic resume generator
python seed.py

# Start FastAPI backend server
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Backend API will be running live at: `http://127.0.0.1:8000` (API Docs at `http://127.0.0.1:8000/docs`).

### 2. Frontend Setup
```bash
# In a new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Frontend Web Dashboard will be live at: `http://127.0.0.1:5173`.

---

## 🧪 Testing & Regression Verification

Run the entire automated test suite:
```bash
# From project root
pytest -v
```
**Status: 71 passed / 0 failed**

Run parser evaluation against ground-truth resumes:
```bash
python scripts/evaluate_parser.py
```
**Status: 100% Accuracy on Synthetic Benchmark Dataset**

Run 500-Candidate Performance Benchmark:
```bash
python scripts/benchmark_perf.py
```

---

## 🚀 The End-to-End Demo Flow

1. **Synthetic Resumes & Ground Truth**: 40 realistic PDF & DOCX resumes parsed and normalized into SQLite.
2. **Indian Academic Normalization**: Correctly extracts 10th %, 12th %, and translates CGPA scales (4.0/5.0/10.0 scale detection) into standardized 10-point metrics with confidence tags.
3. **Job Description & JD Matching**: Match score breakdown: Skills (50%), Experience (25%), Education (15%), TF-IDF Text Similarity (10%).
4. **Recruiter Filters & Presets**: Filter across complex criteria and save reusable presets without modifying source data.
5. **What-If Funnel & Candidate Rescue**: Sequential drop-off waterfall highlighting high-match candidates excluded by rigid thresholds, with one-click requirement relaxation.
6. **Candidate Comparison (2–3 Candidates)**: Side-by-side scorecard, 4-axis Recharts Radar chart (`Skills`, `Experience`, `Education`, `JD Match`), deterministic verdict, and unique/shared skills breakdown.
7. **Evidence-Based Hiring Intelligence & Interview Probes**:
   - Differentiates strong project evidence from weak keyword-stuffing.
   - Computes an explainable Evidence Strength Score (0–100).
   - Generates deterministic interview probes for weak or unverified claims.
   - Renders visual Evidence Chain Graphs.
8. **Multi-Signal Duplicate Detection**: Rapidfuzz-powered duplicate warning comparing email, phone, name similarity, and resume text overlap with a non-destructive review workflow (`Keep Both` vs `Mark Duplicate`).
9. **Blind Review Mode**: One-click bias mitigation concealing candidate names, emails, and phones while retaining ID, competencies, and evidence.
10. **Bulk Email Dispatch Engine (SMTP Dry-Run)**: Safe template-based candidate outreach (`Interview Invitation`, `Shortlist Notification`, `Application Update`) with default `DRY RUN` protection.
11. **Kanban Pipeline & Audit Log**: Drag candidates across pipeline stages (`Applied` → `Shortlisted` → `Interview` → `Offer` / `Rejected`) with full timestamped audit trails.

---

## 🏛 Architecture & Tech Stack

```text
HireSwift ATS
├── Backend (FastAPI + SQLite + SQLAlchemy)
│   ├── app/api/endpoints.py       -> REST API Endpoints
│   ├── app/models/                -> Candidate, Evidence, JDs, AuditLog, Presets
│   ├── app/services/
│   │   ├── resume_parser.py       -> pdfplumber & python-docx parser
│   │   ├── matching_service.py    -> TF-IDF + 4-part score weighting
│   │   ├── skills_service.py      -> Canonical skill synonym mapper & implications
│   │   ├── whatif_service.py      -> Sequential waterfall & rescue algorithms
│   │   ├── comparison_service.py  -> Radar chart & verdict engine
│   │   ├── dedup_service.py       -> Rapidfuzz multi-signal similarity
│   │   ├── intelligence_service.py-> Evidence extraction & interview probes
│   │   ├── email_service.py       -> Safe SMTP Dry-Run engine
│   │   └── export_service.py      -> CSV generator with formula-injection guard
│   └── tests/                     -> 71 Pytest unit & integration tests
│
└── Frontend (React 18 + Vite + Tailwind CSS + Recharts + Lucide Icons)
    ├── src/App.jsx                -> Unified Recruiter Workspace
    └── src/index.css              -> Tailwind typography & styles
```

---

## 🔒 Security & Privacy Guarantees
- **Spreadsheet Security**: CSV exports automatically sanitize formula triggers (`=`, `+`, `-`, `@`, `\t`, `\r`) with single quotes (`'`) preventing CSV injection attacks.
- **Credential Protection**: SMTP engine strictly defaults to `DRY RUN`. Passwords and credentials are never logged, serialized, or exposed to the client.
- **Non-Destructive Operations**: Marking candidates as duplicates preserves raw resumes, profile history, and audit records.
- **Zero External AI Dependency**: All parsing, matching, evidence grading, and probe generation run 100% locally on standard open-source Python libraries.
