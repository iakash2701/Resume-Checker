import os
import json
import random
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from docx import Document

# Set seed for reproducibility
random.seed(42)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESUMES_DIR = os.path.join(BASE_DIR, "data", "resumes")
GROUND_TRUTH_PATH = os.path.join(BASE_DIR, "data", "ground_truth.json")

os.makedirs(RESUMES_DIR, exist_ok=True)

COLLEGES = [
    "PSG College of Technology, Coimbatore",
    "Thiagarajar College of Engineering, Madurai",
    "Vellore Institute of Technology, Chennai",
    "Bannari Amman Institute of Technology, Sathyamangalam",
    "SSN College of Engineering, Kalavakkam",
    "Coimbatore Institute of Technology, Coimbatore",
    "Amrita Vishwa Vidyapeetham, Coimbatore",
    "Kongu Engineering College, Perundurai",
    "Kumaraguru College of Technology, Coimbatore",
    "Sri Krishna College of Engineering and Technology, Coimbatore",
    "RV College of Engineering, Bengaluru",
    "PES University, Bengaluru",
    "SRM Institute of Science and Technology, Kattankulathur",
    "Manipal Institute of Technology, Manipal"
]

DEGREES = [
    "B.Tech Artificial Intelligence and Machine Learning",
    "B.E. Computer Science Engineering",
    "B.Tech Information Technology",
    "B.E. Electronics and Communication Engineering",
    "MCA",
    "B.Sc Computer Science"
]

ALL_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "React", "React.js",
    "Node", "Node.js", "SQL", "MySQL", "PostgreSQL", "MongoDB",
    "FastAPI", "Django", "Flask", "Power BI", "Tableau",
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
    "Docker", "AWS", "Git", "GitHub", "Linux", "HTML", "CSS"
]

NAMES = [
    "Akash Kumar", "Priya Sharma", "Rahul Krishnan", "Harish Kumar", "Divya S",
    "Sanjay R", "Ananya Iyer", "Naveen Raj", "Karthik M", "Keerthana S",
    "Vignesh P", "Deepika V", "Aditya Nair", "Sneha R", "Ganesh K",
    "Pooja Mohan", "Manoj Kumar", "Swetha B", "Arun Prakash", "Meera Krishnan",
    "Aravind Swamy", "Sandhya R", "Ashwin Kumar", "Kavitha M", "Suresh G",
    "Lavanya S", "Pranav V", "Nithya R", "Rajeshwari S", "Vijay Anand",
    "Rohan Gupta", "Shreya Sen", "Varun Teja", "Tanvi Joshi", "Nikhil Verma",
    "Pavithra M", "Kishore Kumar", "Preeti Shenoy", "Vishal K", "Shruti Raman"
]

TENTH_LABELS = [
    "10th Standard", "Class X", "SSC Board", "Matriculation Examination",
    "10th Grade", "Secondary School Certificate", "Xth Standard"
]

TWELFTH_LABELS = [
    "12th Standard", "Class XII", "HSC Examination", "Higher Secondary",
    "Intermediate Board", "XIIth Standard", "Senior Secondary Certificate"
]

def format_percentage(val, label):
    patterns = [
        f"{label}: {val}%",
        f"{label} - {val} %",
        f"{label} Percentage: {val}",
        f"{label} scored {val}% marks",
        f"{label}: {val} percent"
    ]
    return random.choice(patterns)

def format_cgpa(cgpa_10):
    mode = random.choice(["10_scale", "4_scale", "ambiguous", "plain"])
    if mode == "10_scale":
        patterns = [
            f"CGPA: {cgpa_10}",
            f"CGPA {cgpa_10}/10",
            f"CGPA: {cgpa_10} / 10.0",
            f"Cumulative GPA: {cgpa_10} out of 10",
            f"Grade Point Average: {cgpa_10}/10"
        ]
        return random.choice(patterns)
    elif mode == "4_scale":
        gpa_4 = round((cgpa_10 / 10.0) * 4.0, 2)
        patterns = [
            f"GPA: {gpa_4}/4.0",
            f"CGPA (4-pt scale): {gpa_4}/4.0",
            f"{gpa_4} / 4.0 GPA",
            f"Grade Point Average: {gpa_4} on a 4.0 scale"
        ]
        return random.choice(patterns)
    elif mode == "ambiguous":
        return f"CGPA: {cgpa_10}"
    else:
        return f"Overall Academic Score: {cgpa_10} CGPA"

def format_experience(exp):
    if exp == 0.0:
        return random.choice(["Fresher", "Experience: Fresher / None", "Status: Fresher looking for opportunities"])
    elif exp == 0.5:
        return random.choice(["6 months internship experience", "Experience: 6 months", "Completed 6 months training/internship"])
    elif exp == 1.0:
        return random.choice(["1 year of professional experience", "Experience: 1 year", "Worked for 12 months as Software Developer"])
    elif exp == 1.5:
        return random.choice(["1.5 years experience", "Experience: 1.5 years", "Worked for 18 months in tech industry"])
    elif exp == 2.0:
        return random.choice(["2 years of professional experience", "Experience: 2 years", "24 months relevant software experience"])
    else:
        return random.choice([f"{exp} years of full-time experience", f"Total Experience: {exp} years", f"Over {exp} years in software engineering"])

def generate_pdf(filepath, lines):
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, lines[0])  # Name
    y -= 25
    c.setFont("Helvetica", 10)
    for line in lines[1:]:
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
        c.drawString(50, y, line)
        y -= 16
    c.save()

def generate_docx(filepath, lines):
    doc = Document()
    p_name = doc.add_paragraph()
    run = p_name.add_run(lines[0])
    run.bold = True
    run.font.size = docx_size(14)
    for line in lines[1:]:
        doc.add_paragraph(line)
    doc.save(filepath)

def docx_size(pt):
    from docx.shared import Pt
    return Pt(pt)

def generate_all():
    candidates = []
    
    # 40 records: 25 PDF (1..25), 15 DOCX (26..40)
    # Special cases:
    # Duplicates (3 resumes): Candidate 2 duplicate of Candidate 1, Candidate 3 duplicate of Candidate 1
    # Missing fields (3 resumes): Candidate 10 (no 10th pct), Candidate 11 (no CGPA), Candidate 12 (no grad year)

    for i in range(1, 41):
        idx_str = f"{i:03d}"
        ext = "pdf" if i <= 25 else "docx"
        filename = f"resume_{idx_str}.{ext}"
        
        if i == 1:
            # Base for duplicates
            name = "Rahul Kumar"
            email = "rahul.kumar@example.com"
            phone = "9876543210"
            location = "Bengaluru, India"
            college = "PSG College of Technology, Coimbatore"
            degree = "B.E. Computer Science Engineering"
            grad_year = 2024
            tenth_pct = 88.5
            twelfth_pct = 86.0
            cgpa_10 = 8.6
            years_experience = 2.0
            skills = ["Python", "FastAPI", "React", "PostgreSQL", "Docker", "Git"]
        elif i == 2:
            # Duplicate A: Exact email/phone, slightly abbreviated name
            name = "Rahul K"
            email = "rahul.kumar@example.com"
            phone = "9876543210"
            location = "Bangalore, KA"
            college = "PSG College of Technology"
            degree = "B.E. Computer Science"
            grad_year = 2024
            tenth_pct = 88.5
            twelfth_pct = 86.0
            cgpa_10 = 8.6
            years_experience = 2.0
            skills = ["Python", "FastAPI", "React.js", "PostgreSQL", "Docker", "Git"]
        elif i == 3:
            # Duplicate B: Similar text, slightly different formatting
            name = "Rahul Kumar"
            email = "rahulkumar.dev@example.com"
            phone = "+91 9876543210"
            location = "Bengaluru"
            college = "PSG Tech Coimbatore"
            degree = "Bachelor of Engineering - Computer Science"
            grad_year = 2024
            tenth_pct = 88.5
            twelfth_pct = 86.0
            cgpa_10 = 8.6
            years_experience = 2.0
            skills = ["Python", "FastAPI", "React", "SQL", "Docker", "Git"]
        elif i == 10:
            # Missing 10th percentage
            name = NAMES[i - 1]
            email = f"{name.lower().replace(' ', '.')}@example.com"
            phone = f"9{random.randint(100000000, 999999999)}"
            location = random.choice(["Chennai", "Bengaluru", "Hyderabad", "Coimbatore", "Pune"])
            college = random.choice(COLLEGES)
            degree = random.choice(DEGREES)
            grad_year = random.choice([2024, 2025, 2026, 2027, 2028])
            tenth_pct = None  # Missing
            twelfth_pct = round(random.uniform(70.0, 95.0), 1)
            cgpa_10 = round(random.uniform(6.5, 9.8), 2)
            years_experience = random.choice([0.0, 0.5, 1.0, 1.5, 2.0, 3.0])
            skills = random.sample(ALL_SKILLS, random.randint(4, 7))
        elif i == 11:
            # Missing CGPA
            name = NAMES[i - 1]
            email = f"{name.lower().replace(' ', '.')}@example.com"
            phone = f"9{random.randint(100000000, 999999999)}"
            location = random.choice(["Chennai", "Bengaluru", "Hyderabad", "Coimbatore", "Pune"])
            college = random.choice(COLLEGES)
            degree = random.choice(DEGREES)
            grad_year = random.choice([2024, 2025, 2026, 2027, 2028])
            tenth_pct = round(random.uniform(70.0, 95.0), 1)
            twelfth_pct = round(random.uniform(70.0, 95.0), 1)
            cgpa_10 = None  # Missing
            years_experience = random.choice([0.0, 0.5, 1.0, 1.5, 2.0, 3.0])
            skills = random.sample(ALL_SKILLS, random.randint(4, 7))
        elif i == 12:
            # Missing grad year
            name = NAMES[i - 1]
            email = f"{name.lower().replace(' ', '.')}@example.com"
            phone = f"9{random.randint(100000000, 999999999)}"
            location = random.choice(["Chennai", "Bengaluru", "Hyderabad", "Coimbatore", "Pune"])
            college = random.choice(COLLEGES)
            degree = random.choice(DEGREES)
            grad_year = None  # Missing
            tenth_pct = round(random.uniform(70.0, 95.0), 1)
            twelfth_pct = round(random.uniform(70.0, 95.0), 1)
            cgpa_10 = round(random.uniform(6.5, 9.8), 2)
            years_experience = random.choice([0.0, 0.5, 1.0, 1.5, 2.0, 3.0])
            skills = random.sample(ALL_SKILLS, random.randint(4, 7))
        else:
            name = NAMES[i - 1]
            email = f"{name.lower().replace(' ', '.')}@example.com"
            phone = f"9{random.randint(100000000, 999999999)}"
            location = random.choice(["Chennai", "Bengaluru", "Hyderabad", "Coimbatore", "Pune", "Kochi", "Mumbai"])
            college = random.choice(COLLEGES)
            degree = random.choice(DEGREES)
            grad_year = random.choice([2024, 2025, 2026, 2027, 2028, 2029])
            tenth_pct = round(random.uniform(70.0, 96.0), 1)
            twelfth_pct = round(random.uniform(70.0, 96.0), 1)
            cgpa_10 = round(random.uniform(6.5, 9.8), 2)
            years_experience = random.choice([0.0, 0.5, 1.0, 1.5, 2.0, 3.0])
            skills = random.sample(ALL_SKILLS, random.randint(4, 7))

        candidate_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "location": location,
            "college": college,
            "degree": degree,
            "grad_year": grad_year,
            "tenth_pct": tenth_pct,
            "twelfth_pct": twelfth_pct,
            "cgpa_10": cgpa_10,
            "years_experience": years_experience,
            "skills": skills,
            "filename": filename
        }
        candidates.append(candidate_data)

    ground_truth = {}

    for cand in candidates:
        fn = cand["filename"]
        ground_truth[fn] = {
            "name": cand["name"],
            "email": cand["email"],
            "phone": cand["phone"],
            "location": cand["location"],
            "college": cand["college"],
            "degree": cand["degree"],
            "grad_year": cand["grad_year"],
            "tenth_pct": cand["tenth_pct"],
            "twelfth_pct": cand["twelfth_pct"],
            "cgpa_10": cand["cgpa_10"],
            "years_experience": cand["years_experience"],
            "skills": cand["skills"]
        }

        # Build resume text lines
        lines = [
            cand["name"].upper(),
            f"Email: {cand['email']} | Contact: {cand['phone']} | Location: {cand['location']}",
            "--------------------------------------------------------------------------------",
            "SUMMARY & OBJECTIVE",
            f"Aspiring software and technology professional specializing in {cand['degree']}.",
            format_experience(cand["years_experience"]),
            "--------------------------------------------------------------------------------",
            "EDUCATION"
        ]

        # Degree & College
        grad_txt = f" (Graduation: {cand['grad_year']})" if cand["grad_year"] else ""
        lines.append(f"{cand['degree']}{grad_txt}")
        lines.append(f"Institution: {cand['college']}")

        if cand["cgpa_10"] is not None:
            lines.append(format_cgpa(cand["cgpa_10"]))

        if cand["twelfth_pct"] is not None:
            t12_lbl = random.choice(TWELFTH_LABELS)
            lines.append(format_percentage(cand["twelfth_pct"], t12_lbl))

        if cand["tenth_pct"] is not None:
            t10_lbl = random.choice(TENTH_LABELS)
            lines.append(format_percentage(cand["tenth_pct"], t10_lbl))

        lines.extend([
            "--------------------------------------------------------------------------------",
            "TECHNICAL SKILLS",
            f"Proficiencies: {', '.join(cand['skills'])}",
            "Tools & Technologies: Git, VSCode, Terminal, Postman",
            "--------------------------------------------------------------------------------",
            "PROJECTS & HIGHLIGHTS",
            f"1. Scalable Cloud Architecture - Implemented using {', '.join(cand['skills'][:2])}."
        ])

        filepath = os.path.join(RESUMES_DIR, fn)
        if fn.endswith(".pdf"):
            generate_pdf(filepath, lines)
        else:
            generate_docx(filepath, lines)

    with open(GROUND_TRUTH_PATH, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    print(f"Generated 40 resumes in {RESUMES_DIR}")
    print(f"Generated ground truth at {GROUND_TRUTH_PATH}")

if __name__ == "__main__":
    generate_all()
