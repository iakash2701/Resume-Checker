import os
import sys
import json
from typing import Dict, Any, List

# Ensure backend root is in python path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.resume_parser import parse_resume

def evaluate_dataset(resumes_dir: str, ground_truth_path: str, dataset_name: str) -> Dict[str, Any]:
    if not os.path.exists(ground_truth_path):
        return {"status": "missing", "name": dataset_name}

    with open(ground_truth_path, "r", encoding="utf-8") as f:
        ground_truth: Dict[str, Any] = json.load(f)

    total_files = len(ground_truth)
    if total_files == 0:
        return {"status": "empty", "name": dataset_name}

    metrics = {
        "tenth_pct": {"correct": 0, "total": 0},
        "twelfth_pct": {"correct": 0, "total": 0},
        "cgpa_10": {"correct": 0, "total": 0},
        "grad_year": {"correct": 0, "total": 0},
        "years_experience": {"correct": 0, "total": 0},
        "skills": {"correct": 0, "total": 0}
    }
    
    mismatches = []
    float_tolerance = 0.05

    for filename, expected in ground_truth.items():
        file_path = os.path.join(resumes_dir, filename)
        if not os.path.exists(file_path):
            continue

        parsed = parse_resume(file_path)
        evidence_dict = {ev["field_name"]: ev for ev in parsed.get("evidence", [])}

        # 1. 10th
        metrics["tenth_pct"]["total"] += 1
        exp_tenth = expected.get("tenth_pct")
        got_tenth = parsed.get("tenth_pct")
        tenth_conf = evidence_dict.get("tenth_pct", {}).get("confidence", "low")
        if exp_tenth is None:
            if got_tenth is None:
                metrics["tenth_pct"]["correct"] += 1
            else:
                mismatches.append({"file": filename, "field": "tenth_pct", "expected": None, "got": got_tenth, "confidence": tenth_conf})
        else:
            if got_tenth is not None and abs(exp_tenth - got_tenth) <= float_tolerance:
                metrics["tenth_pct"]["correct"] += 1
            else:
                mismatches.append({"file": filename, "field": "tenth_pct", "expected": exp_tenth, "got": got_tenth, "confidence": tenth_conf})

        # 2. 12th
        metrics["twelfth_pct"]["total"] += 1
        exp_twelfth = expected.get("twelfth_pct")
        got_twelfth = parsed.get("twelfth_pct")
        twelfth_conf = evidence_dict.get("twelfth_pct", {}).get("confidence", "low")
        if exp_twelfth is None:
            if got_twelfth is None:
                metrics["twelfth_pct"]["correct"] += 1
            else:
                mismatches.append({"file": filename, "field": "twelfth_pct", "expected": None, "got": got_twelfth, "confidence": twelfth_conf})
        else:
            if got_twelfth is not None and abs(exp_twelfth - got_twelfth) <= float_tolerance:
                metrics["twelfth_pct"]["correct"] += 1
            else:
                mismatches.append({"file": filename, "field": "twelfth_pct", "expected": exp_twelfth, "got": got_twelfth, "confidence": twelfth_conf})

        # 3. CGPA
        metrics["cgpa_10"]["total"] += 1
        exp_cgpa = expected.get("cgpa_10")
        got_cgpa = parsed.get("cgpa_10")
        cgpa_conf = evidence_dict.get("cgpa_10", {}).get("confidence", "low")
        if exp_cgpa is None:
            if got_cgpa is None:
                metrics["cgpa_10"]["correct"] += 1
            else:
                mismatches.append({"file": filename, "field": "cgpa_10", "expected": None, "got": got_cgpa, "confidence": cgpa_conf})
        else:
            if got_cgpa is not None and abs(exp_cgpa - got_cgpa) <= float_tolerance:
                metrics["cgpa_10"]["correct"] += 1
            else:
                mismatches.append({"file": filename, "field": "cgpa_10", "expected": exp_cgpa, "got": got_cgpa, "confidence": cgpa_conf})

        # 4. Grad Year
        metrics["grad_year"]["total"] += 1
        exp_year = expected.get("grad_year")
        got_year = parsed.get("grad_year")
        if exp_year == got_year:
            metrics["grad_year"]["correct"] += 1
        else:
            mismatches.append({"file": filename, "field": "grad_year", "expected": exp_year, "got": got_year, "confidence": "high"})

        # 5. Experience
        metrics["years_experience"]["total"] += 1
        exp_exp = float(expected.get("years_experience", 0.0) or 0.0)
        got_exp = float(parsed.get("years_experience", 0.0) or 0.0)
        if abs(exp_exp - got_exp) <= float_tolerance:
            metrics["years_experience"]["correct"] += 1
        else:
            mismatches.append({"file": filename, "field": "years_experience", "expected": exp_exp, "got": got_exp, "confidence": "high"})

        # 6. Skills
        metrics["skills"]["total"] += 1
        exp_skills = set(expected.get("skills", []))
        got_skills = set(parsed.get("skills", []))
        norm_exp = {s.lower().replace(".js", "") for s in exp_skills}
        norm_got = {s.lower().replace(".js", "") for s in got_skills}
        intersection = norm_exp.intersection(norm_got)
        recall = len(intersection) / len(norm_exp) if norm_exp else 1.0
        if recall >= 0.8:
            metrics["skills"]["correct"] += 1
        else:
            mismatches.append({"file": filename, "field": "skills", "expected": list(exp_skills), "got": list(got_skills), "confidence": "high"})

    return {
        "status": "evaluated",
        "name": dataset_name,
        "total_files": total_files,
        "metrics": metrics,
        "mismatches": mismatches
    }

def print_dataset_report(result: Dict[str, Any]):
    print(f"\n--- {result['name'].upper()} DATASET EVALUATION ---")
    if result["status"] == "missing":
        print(f"Dataset not found (held-out data waiting to be populated).")
        return
    elif result["status"] == "empty":
        print("Dataset is empty.")
        return

    print(f"Files evaluated: {result['total_files']}\n")
    print(f"{'Field':<25} {'Accuracy':<10} {'Status'}")
    print("-" * 50)

    for key, label in [
        ("tenth_pct", "10th Percentage"),
        ("twelfth_pct", "12th Percentage"),
        ("cgpa_10", "CGPA"),
        ("grad_year", "Graduation Year"),
        ("skills", "Skills"),
        ("years_experience", "Experience")
    ]:
        m = result["metrics"][key]
        acc = (m["correct"] / m["total"]) * 100 if m["total"] > 0 else 0
        status_icon = "[PASS]" if acc >= 90.0 else "[WARN]"
        print(f"{label:<25} {acc:>6.1f}%     {status_icon}")

    print("\nMismatch Summary & Risk Analysis:")
    mismatches = result["mismatches"]
    if not mismatches:
        print("  None (100% match across all evaluated fields)")
    else:
        high_risk = [m for m in mismatches if m["confidence"] == "high"]
        med_risk = [m for m in mismatches if m["confidence"] == "medium"]
        low_risk = [m for m in mismatches if m["confidence"] == "low"]

        print(f"  Total Mismatches: {len(mismatches)}")
        print(f"  High Confidence Mismatches (DANGEROUS): {len(high_risk)}")
        print(f"  Medium Confidence Mismatches:         {len(med_risk)}")
        print(f"  Low Confidence Mismatches (FLAGGED):    {len(low_risk)}")

        print("\n  List of Mismatches:")
        for m in mismatches:
            print(f"   * File: {m['file']} | Field: {m['field']} | Expected: {m['expected']} | Got: {m['got']} | Confidence: {m['confidence']}")

def evaluate():
    print("=" * 60)
    print("HIRESWIFT PARSER COMPREHENSIVE EVALUATION")
    print("=" * 60)

    # 1. Synthetic Dataset
    syn_resumes = os.path.join(BASE_DIR, "data", "resumes")
    syn_gt = os.path.join(BASE_DIR, "data", "ground_truth.json")
    syn_result = evaluate_dataset(syn_resumes, syn_gt, "Synthetic Benchmark")
    print_dataset_report(syn_result)

    # 2. Real Held-Out Dataset
    real_resumes = os.path.join(BASE_DIR, "data", "real_resumes")
    real_gt = os.path.join(BASE_DIR, "data", "ground_truth_real.json")
    real_result = evaluate_dataset(real_resumes, real_gt, "Real Held-Out Benchmark")
    print_dataset_report(real_result)

    print("=" * 60 + "\n")

if __name__ == "__main__":
    evaluate()
