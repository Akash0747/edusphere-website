"""Build src/data/archive.json from the GitHub repo's seed_data.sql plus
verified official question-paper links.

Sources (all checked on 2026-11-03):
  * repo-seed.json       — 30 papers + 2 mock questions parsed out of
                           edusphere-backend/seed_data.sql @ 9607a80
  * cbse-links.json      — cbse.gov.in/cbsenew/question-paper.html (XII files)
  * jeemain-links.json   — jeemain.nta.nic.in/sitemap/ "Question Papers"
  * jeeadv.ac.in/archive.html past_qps pattern (hard-coded below)
  * Official / verified archive pages for NEET UG and ISC Class 12

Run:  python3 build_data.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "src" / "data"
DATA.mkdir(parents=True, exist_ok=True)

seed = json.loads((DATA / "repo-seed.json").read_text())
cbse_links = json.loads((DATA / "cbse-links.json").read_text())
jm_links = json.loads((DATA / "jeemain-links.json").read_text())

EXAMS = [
    {
        "id": "isc-12",
        "name": "ISC Class 12",
        "board": "CISCE",
        "short": "ISC XII",
        "blurb": "Council for the Indian School Certificate Examinations — Class XII board papers and specimen papers.",
        "tag": "BOARD",
        "colour": "#8d6b45",
    },
    {
        "id": "cbse-12",
        "name": "CBSE Class 12",
        "board": "CBSE",
        "short": "CBSE XII",
        "blurb": "Central Board of Secondary Education — Class XII board question papers, subject-wise and year-wise.",
        "tag": "BOARD",
        "colour": "#b06b3a",
    },
    {
        "id": "jee-main",
        "name": "JEE Main",
        "board": "NTA",
        "short": "JEE MAIN",
        "blurb": "Joint Entrance Examination (Main) — B.E./B.Tech shift-wise papers published by the National Testing Agency.",
        "tag": "ENTRANCE",
        "colour": "#5c6f86",
    },
    {
        "id": "jee-advanced",
        "name": "JEE Advanced",
        "board": "IIT",
        "short": "JEE ADV",
        "blurb": "The official IIT JEE (Advanced) past question paper archive — Paper 1 and Paper 2, 2007 onwards.",
        "tag": "ENTRANCE",
        "colour": "#6b5b8a",
    },
    {
        "id": "neet",
        "name": "NEET UG",
        "board": "NTA",
        "short": "NEET UG",
        "blurb": "National Eligibility cum Entrance Test — undergraduate medical question papers, code-wise sets.",
        "tag": "ENTRANCE",
        "colour": "#4f7160",
    },
    {
        "id": "cbse-10",
        "name": "CBSE Class 10",
        "board": "CBSE",
        "short": "CBSE X",
        "blurb": "Class X papers also present in the repository database.",
        "tag": "EXTRA",
        "colour": "#8a7359",
    },
    {
        "id": "icse-10",
        "name": "ICSE Class 10",
        "board": "CISCE",
        "short": "ICSE X",
        "blurb": "Class X specimen papers also present in the repository database.",
        "tag": "EXTRA",
        "colour": "#7a6a58",
    },
]

TOPICS = {
    "Physics": ["Mechanics", "Electrostatics", "Optics", "Modern Physics"],
    "Chemistry": ["Physical Chemistry", "Organic Chemistry", "Inorganic Chemistry"],
    "Mathematics": ["Algebra", "Calculus", "Probability", "Coordinate Geometry"],
    "Biology": ["Botany", "Zoology", "Genetics", "Human Physiology"],
    "English Core": ["Reading Comprehension", "Writing Skills", "Literature"],
    "English": ["Reading Comprehension", "Writing Skills", "Literature"],
    "Economics": ["Microeconomics", "Macroeconomics", "Indian Economy"],
    "Accountancy": ["Financial Statements", "Partnership", "Cash Flow"],
    "Computer Science": ["Programming", "Data Structures", "Boolean Algebra"],
    "Applied Mathematics": ["Calculus", "Probability", "Linear Programming"],
    "Business Studies": ["Management", "Marketing", "Finance"],
    "History": ["Ancient India", "Modern India", "World History"],
    "Psychology": ["Cognitive Processes", "Personality", "Social Psychology"],
    "Science": ["Physics", "Chemistry", "Biology"],
    "Social Science": ["History", "Geography", "Political Science"],
    "Physics, Chemistry & Mathematics": ["Physics", "Chemistry", "Mathematics"],
    "Physics, Chemistry & Biology": ["Physics", "Chemistry", "Biology"],
}

papers: list[dict] = []


def add(**kw):
    rec = {
        "id": f"p{len(papers) + 1:03d}",
        "exam": kw["exam"],
        "year": int(kw["year"]),
        "subject": kw["subject"],
        "session": kw.get("session", ""),
        "title": kw["title"],
        "description": kw.get("description", ""),
        "type": kw.get("type", "Question Paper"),
        "format": kw.get("format", "link"),
        "sourceUrl": kw["sourceUrl"],
        "sourceLabel": kw.get("sourceLabel", "Official source"),
        "fileName": kw.get("fileName", ""),
        "origin": kw.get("origin", "curated"),
        "downloads": int(kw.get("downloads", 0)),
        "featured": bool(kw.get("featured", True)),
        "verified": bool(kw.get("verified", True)),
        "note": kw.get("note", ""),
    }
    rec["topics"] = TOPICS.get(rec["subject"], TOPICS.get(rec["subject"].split(",")[0], []))
    papers.append(rec)


# ---------------------------------------------------------------------------
# 1. Everything from the GitHub repository's seed_data.sql
# ---------------------------------------------------------------------------
# ncert.nic.in did not respond from the build environment on 2026-11-03.
# The rows are kept verbatim, but flagged so the UI can be honest about them.
UNREACHABLE = ("ncert.nic.in",)

for row in seed["papers"]:
    url = row["source_url"]
    fmt = "pdf" if url.lower().endswith(".pdf") else "archive"
    reachable = not any(host in url for host in UNREACHABLE)
    typ = "Question Paper"
    if re.search(r"solution|marking scheme|answer key", row["title"], re.I):
        typ = "Marking Scheme"
    elif "SQP" in row["session"] or "Specimen" in row["session"]:
        typ = "Sample / Specimen Paper"
    elif "NCERT" in row["session"]:
        typ = "Textbook Chapter"
    add(
        exam=row["exam"],
        year=row["year"],
        subject=row["subject"],
        session=row["session"],
        title=row["title"],
        description=row["description"],
        type=typ,
        format=fmt,
        sourceUrl=url,
        sourceLabel="seed_data.sql · external source",
        fileName=row["file_name"],
        origin="repo",
        downloads=row["downloads"],
        verified=reachable,
        note=(
            "Loaded verbatim from the repository database (seed_data.sql). "
            "The official NCERT host was unreachable when this archive was "
            "built (2026-11-03); retry later or use the NCERT textbook portal."
            if not reachable
            else "Loaded verbatim from the repository database (seed_data.sql)."
        ),
    )

# ---------------------------------------------------------------------------
# 2. CBSE Class XII — official cbse.gov.in question papers, 2022–2025
# ---------------------------------------------------------------------------
for year, subjects in cbse_links.items():
    for subject, url in subjects.items():
        fmt = "pdf" if url.lower().endswith(".pdf") else "zip"
        add(
            exam="cbse-12",
            year=year,
            subject=subject,
            session="Board Examination",
            title=f"CBSE Class 12 {subject} — {year} Board Question Paper",
            description=(
                f"Official {year} Class XII {subject} board examination question "
                "paper published by CBSE. "
                + ("Direct PDF. " if fmt == "pdf" else "ZIP bundle containing the paper set(s). ")
            ),
            type="Question Paper",
            format=fmt,
            sourceUrl=url,
            sourceLabel="cbse.gov.in · official",
            fileName=url.rsplit("/", 1)[-1],
            origin="official",
            note=(
                "Official CBSE archive. ZIP bundles may contain multiple question "
                "paper sets and marking schemes."
            ),
        )

# ---------------------------------------------------------------------------
# 3. JEE Advanced — official jeeadv.ac.in past_qps archive
# ---------------------------------------------------------------------------
for year in range(2014, 2026):
    lang = "_English" if year >= 2019 else ""
    for paper_no in (1, 2):
        url = f"https://jeeadv.ac.in/past_qps/{year}_{paper_no}{lang}.pdf"
        add(
            exam="jee-advanced",
            year=year,
            subject="Physics, Chemistry & Mathematics",
            session=f"Paper {paper_no}",
            title=f"JEE Advanced {year} — Paper {paper_no} (English)",
            description=(
                f"Official JEE (Advanced) {year} Paper {paper_no} question paper "
                "from the JEE Advanced past question papers archive."
            ),
            type="Question Paper",
            format="pdf",
            sourceUrl=url,
            sourceLabel="jeeadv.ac.in · official archive",
            fileName=f"{year}_{paper_no}{lang}.pdf",
            origin="official",
        )
for year in (2023, 2024):
    add(
        exam="jee-advanced",
        year=year,
        subject="Physics, Chemistry & Mathematics",
        session="Paper 1 · Hindi",
        title=f"JEE Advanced {year} — Paper 1 (Hindi)",
        description=f"Official Hindi-medium JEE (Advanced) {year} Paper 1 question paper.",
        type="Question Paper",
        format="pdf",
        sourceUrl=f"https://jeeadv.ac.in/past_qps/{year}_1_Hindi.pdf",
        sourceLabel="jeeadv.ac.in · official archive",
        fileName=f"{year}_1_Hindi.pdf",
        origin="official",
    )

# ---------------------------------------------------------------------------
# 4. JEE Main — official shift papers listed on the NTA sitemap
# ---------------------------------------------------------------------------
seen = set()
for item in jm_links:
    url = item["url"]
    if url in seen:
        continue
    seen.add(url)
    label = item["label"]
    m = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})\s+Shift\s*(\d)", label)
    if not m:
        continue
    day, month, year, shift = m.groups()
    add(
        exam="jee-main",
        year=int(year),
        subject="Physics, Chemistry & Mathematics",
        session=f"Session 2 · {day} {month} · Shift {shift}",
        title=f"JEE Main {year} — B.Tech {day} {month}, Shift {shift}",
        description=(
            f"Official NTA question paper for JEE (Main) {year} B.E./B.Tech "
            f"Paper 1, {day} {month} {year}, Shift {shift}."
        ),
        type="Question Paper",
        format="pdf",
        sourceUrl=url,
        sourceLabel="jeemain.nta.nic.in · official PDF",
        fileName=url.rsplit("/", 1)[-1],
        origin="official",
    )

JEE_MAIN_PORTALS = [
    (2026, "JEE Main 2026 — Official document archive", "https://jeemain.nta.nic.in/2026-archive/"),
    (2025, "JEE Main 2025 — Official document archive", "https://jeemain.nta.nic.in/document-category/2025-public-notices/"),
    (2024, "JEE Main 2024 — NTA archive & answer-key notices", "https://jeemain.nta.nic.in/documents/"),
    (2023, "JEE Main 2023 — NTA e-services & archive", "https://jeemain.nta.nic.in/e-services-2021/"),
]
for year, title, url in JEE_MAIN_PORTALS:
    add(
        exam="jee-main",
        year=year,
        subject="Physics, Chemistry & Mathematics",
        session="Official NTA archive",
        title=title,
        description="Browse the NTA's official document archive for this session; question papers and answer keys are published here.",
        type="Archive",
        format="archive",
        sourceUrl=url,
        sourceLabel="jeemain.nta.nic.in · official",
        origin="official",
        note="Portal page — open it and choose the question paper for your shift.",
    )

# ---------------------------------------------------------------------------
# 5. NEET UG — NTA official archive + verified PYQ collections
# ---------------------------------------------------------------------------
NEET = [
    (2025, "NEET UG 2025 — Official NTA archive", "Physics, Chemistry & Biology", "Official archive",
     "https://neet.nta.nic.in/neetug-2025/", "neet.nta.nic.in · official", "archive",
     "Official NTA NEET (UG) 2025 document archive."),
    (2024, "NEET UG 2024 — Question papers, all codes (Q/R/S/T)", "Physics, Chemistry & Biology", "Code Q / R / S / T",
     "https://collegedunia.com/exams/neet/question-paper-2024", "PYQ collection · verified", "archive",
     "NTA official 2024 papers reproduced by set code. Some portals restrict automated access; opens normally in a browser."),
    (2024, "NEET UG 2024 — Solved paper & answer key", "Physics, Chemistry & Biology", "Solved set",
     "https://medicine.careers360.com/articles/neet-2024-question-paper-with-solution-pdf", "Careers360 · verified", "archive",
     "2024 question paper with solutions and code-wise answer keys."),
    (2024, "NEET UG 2024 — Set-wise papers with solutions", "Physics, Chemistry & Biology", "Code-wise sets",
     "https://www.aakash.ac.in/blog/neet-2024-question-paper-download-neet-ug-paper-pdf-set-wise/", "Aakash · verified", "archive",
     "All 24 sets (Q1–T6) with solutions."),
    (2024, "NEET UG 2024 — Re-examination paper (23 June)", "Physics, Chemistry & Biology", "Re-exam",
     "https://www.aakash.ac.in/blog/neet-re-exam-2024-question-paper-answer-key-solutions-pdf/", "Aakash · verified", "archive",
     "Question paper and answer key for the 23 June 2024 re-examination."),
    (2023, "NEET UG 2023 — Previous year papers", "Physics, Chemistry & Biology", "Year 2023",
     "https://hive.pracbee.com/neet/previous-year-question-papers", "PracBee · repo allowlist", "archive",
     "Year-wise NEET question paper collection used by the repository's NEET discovery scraper."),
    (2022, "NEET UG 2022 — Previous year papers", "Physics, Chemistry & Biology", "Year 2022",
     "https://docs.aglasem.com/org/nta/neet-ug/question-paper", "AglaSem · repo allowlist", "archive",
     "NEET UG question paper index used by the repository's NEET discovery scraper."),
    (2021, "NEET UG 2021 — Previous year papers", "Physics, Chemistry & Biology", "Year 2021",
     "https://pdf.questions.examgoal.com/past-years/year-wise/medical/neet", "ExamGOAL · repo allowlist", "archive",
     "Year-wise NEET paper index used by the repository's NEET discovery scraper."),
    (2020, "NEET UG 2020 — Previous year papers", "Physics, Chemistry & Biology", "Year 2020",
     "https://neet.nta.nic.in/archive/", "neet.nta.nic.in · official archive", "archive",
     "NTA's official NEET archive (notices, bulletins, answer keys and papers)."),
]
for year, title, subject, session, url, label, fmt, desc in NEET:
    add(exam="neet", year=year, subject=subject, session=session, title=title,
        description=desc, type="Question Paper", format=fmt, sourceUrl=url,
        sourceLabel=label, origin="official" if "nta.nic.in" in url else "verified",
        note="Opens an archive page — choose your set / code there.")

# ---------------------------------------------------------------------------
# 6. ISC Class 12 — CISCE specimen papers + verified PYQ indexes
# ---------------------------------------------------------------------------
ISC_SUBJECTS_2025 = ["Physics", "Chemistry", "Mathematics", "Biology", "English", "Computer Science", "Economics", "Accounts"]
ISC_PAGE = "https://cisce.org/specimen-question-papers-isc-class-xii-2025/"
for subject in ISC_SUBJECTS_2025:
    add(
        exam="isc-12", year=2025, subject=subject, session="Specimen Paper 2025",
        title=f"ISC Class 12 {subject} — Specimen Paper 2025",
        description=f"CISCE's official 2025 ISC Class XII {subject} specimen question paper with marking scheme.",
        type="Sample / Specimen Paper", format="archive", sourceUrl=ISC_PAGE,
        sourceLabel="cisce.org · official", origin="official",
        note="CISCE blocks some non-Indian IPs; if the page is blocked, use the AglaSem mirror listed in this archive.",
    )
ISC_ARCHIVES = [
    (2024, "ISC Class 12 — 2024 specimen & sample papers", "https://docs.aglasem.com/org/cisce/isc/sample-paper?year=2024", "AglaSem · CISCE mirror"),
    (2023, "ISC Class 12 — 2023 previous year papers", "https://docs.aglasem.com/org/cisce/isc/sample-paper?year=2023", "AglaSem · CISCE mirror"),
    (2022, "ISC Class 12 — 2022 specimen papers", "https://docs.aglasem.com/org/cisce/isc/sample-paper?year=2022", "AglaSem · CISCE mirror"),
    (2025, "ISC Class 12 — Previous year question paper index", "https://schools.aglasem.com/104460/", "AglaSem · PYQ index"),
    (2024, "ISC Class 12 — Computer Science PYQ (2025/2024/2023)", "https://schools.aglasem.com/104867/", "AglaSem · subject PYQ"),
    (2026, "CISCE — Official publications & specimen papers", "https://cisce.org/publications.aspx", "cisce.org · official"),
]
for year, title, url, label in ISC_ARCHIVES:
    add(exam="isc-12", year=year, subject="All Subjects", session="Archive", title=title,
        description="ISC Class XII previous year / specimen question paper index. Choose your subject and year on the source page.",
        type="Archive", format="archive", sourceUrl=url, sourceLabel=label,
        origin="verified", note="Index page — pick the subject paper on the source site.")

# ---------------------------------------------------------------------------
# 7. Practice question bank (2 verbatim DB questions + illustrative practice)
# ---------------------------------------------------------------------------
questions = []
for row in seed["mock_tests"]:
    questions.append({
        "id": f"q{len(questions) + 1:03d}",
        "exam": row["exam"],
        "subject": row["subject"],
        "origin": "repo",
        "source": "seed_data.sql · mock_tests",
        "question": row["question"],
        "options": [row["option_a"], row["option_b"], row["option_c"], row["option_d"]],
        "answer": "ABCD".index(row["correct_option"].strip()[:1].upper()),
        "explanation": row["explanation"],
        "officialSource": row["official_source"],
    })

PRACTICE = [
    ("jee-main", "Physics", "A body of mass 2 kg moves with a constant speed of 5 m/s in a circle of radius 1 m. The centripetal force acting on it is:",
     ["10 N", "25 N", "50 N", "100 N"], 2,
     "F = mv²/r = 2 × 25 / 1 = 50 N."),
    ("jee-main", "Chemistry", "Which of the following has the highest first ionisation enthalpy?",
     ["Sodium", "Magnesium", "Aluminium", "Silicon"], 3,
     "Ionisation enthalpy increases across a period; silicon (group 14) is highest among these period-3 elements."),
    ("jee-advanced", "Mathematics", "The number of real solutions of the equation |x − 2| + |x + 1| = 3 is:",
     ["0", "1", "2", "Infinitely many"], 3,
     "For −1 ≤ x ≤ 2 the sum is exactly 3, so every x in that closed interval is a solution — infinitely many."),
    ("jee-advanced", "Physics", "A particle is projected at 45° with speed u. The ratio of its maximum height to its horizontal range is:",
     ["1 : 2", "1 : 4", "1 : 1", "2 : 1"], 1,
     "H = u²sin²θ/2g = u²/4g and R = u²sin2θ/g = u²/g, so H : R = 1 : 4."),
    ("neet", "Biology", "The site of the light reaction of photosynthesis in a chloroplast is the:",
     ["Stroma", "Thylakoid membrane", "Outer membrane", "Matrix"], 1,
     "Light reactions occur on the thylakoid membranes where chlorophyll and the electron transport chain are located."),
    ("neet", "Biology", "Which blood cells are chiefly responsible for the clotting of blood?",
     ["Erythrocytes", "Lymphocytes", "Platelets", "Neutrophils"], 2,
     "Platelets (thrombocytes) release thromboplastin and aggregate to form the platelet plug."),
    ("cbse-12", "Mathematics", "If A is a square matrix of order 3 and |A| = 5, then |adj A| equals:",
     ["5", "25", "125", "1/5"], 1,
     "|adj A| = |A|^(n−1) = 5² = 25 for n = 3."),
    ("cbse-12", "Physics", "The SI unit of electric flux is:",
     ["N/C", "N·m²/C", "V/m", "C/m²"], 1,
     "Electric flux Φ = E·A, so its unit is (N/C)·m² = N·m²/C, equivalently V·m."),
    ("isc-12", "Physics", "A convex lens of focal length 20 cm forms a real image twice the size of the object. The object distance is:",
     ["10 cm", "20 cm", "30 cm", "60 cm"], 2,
     "m = −2 = v/u → v = −2u with sign convention; using 1/f = 1/v − 1/u gives u = −30 cm, i.e. 30 cm."),
    ("isc-12", "Chemistry", "Which of the following is a colligative property?",
     ["Refractive index", "Elevation in boiling point", "Density", "Viscosity"], 1,
     "Colligative properties depend only on the number of solute particles; elevation of boiling point is one of them."),
]
for exam, subject, q, opts, ans, expl in PRACTICE:
    questions.append({
        "id": f"q{len(questions) + 1:03d}", "exam": exam, "subject": subject,
        "origin": "practice", "source": "Illustrative practice set (not an official paper)",
        "question": q, "options": opts, "answer": ans, "explanation": expl,
        "officialSource": "Practice set — illustrative question",
    })

# ---------------------------------------------------------------------------
counts = {}
for p in papers:
    counts[p["exam"]] = counts.get(p["exam"], 0) + 1
out = {
    "meta": {
        "title": "EduSphere Question Paper Archive",
        "generated": "2026-11-03",
        "repo": "https://github.com/Akash0747/edusphere-website",
        "repoCommit": "9607a80",
        "database": "seed_data.sql (papers + mock_tests), bundled as JSON",
        "note": "Papers marked 'repo' are verbatim rows from seed_data.sql. Others are curated links to official/verified paper archives.",
    },
    "exams": EXAMS,
    "papers": papers,
    "questions": questions,
    "counts": counts,
}
(DATA / "archive.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(f"Wrote {len(papers)} papers, {len(questions)} questions")
print("By exam:", counts)
print("By origin:", {o: sum(1 for p in papers if p["origin"] == o) for o in {p["origin"] for p in papers}})
print("By format:", {f: sum(1 for p in papers if p["format"] == f) for f in {p["format"] for p in papers}})
