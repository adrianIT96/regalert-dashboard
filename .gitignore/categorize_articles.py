import sqlite3

DB_PATH = "data/regalert_data.sqlite"

# =========================
# TAXONOMY
# =========================
TAXONOMY = [
    ("Data_Privacy", ["gdpr", "privacy", "hipaa", "data protection"]),
    ("Cybersecurity", ["cyber", "security", "ransomware", "breach", "encryption"]),
    ("Clinical_Trials", ["clinical trial", "phase i", "phase ii", "phase iii", "randomized"]),
    ("SaMD", ["software as a medical device", "samd"]),
    ("Post_Market_Surveillance", ["post-market", "surveillance", "vigilance", "recall"]),
    ("AI_Regulation", ["regulation", "regulatory", "compliance", "approval", "ce mark", "fda"]),
    ("Regulatory_Compliance", ["regulatory framework", "guideline"]),
    ("Imaging_Devices", ["imaging", "radiology", "ct", "mri", "ultrasound"]),
    ("Genomics", ["genomic", "genome", "sequencing", "dna", "rna", "variant", "mutation"]),
    ("Biomarkers", ["biomarker", "marker", "signature"]),
    ("Diagnostics", ["diagnostic", "diagnosis", "screening", "detection"]),
    ("Pathology", ["pathology", "histopathology", "slide", "tissue"]),
    ("Decision_Support", ["decision support", "clinical decision", "cdss"]),
    ("Risk_Prediction", ["risk prediction", "risk model", "prognosis", "prognostic"]),
    ("Digital_Health", ["digital health", "mobile health", "mhealth", "telemedicine", "wearable"]),
    ("AI_Adoption", ["artificial intelligence", "machine learning", "deep learning", "ai "]),
]

# =========================
# DB
# =========================
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Add column if not exists
try:
    cur.execute("ALTER TABLE pubmed_articles ADD COLUMN Category_V2 TEXT")
    conn.commit()
except:
    pass

# =========================
# CLASSIFY
# =========================
def classify(title: str):
    t = title.lower()

    for category, keywords in TAXONOMY:
        for kw in keywords:
            if kw in t:
                return category

    return "Other"

# =========================
# RUN
# =========================
cur.execute("SELECT id, Title FROM pubmed_articles")
rows = cur.fetchall()

updated = 0

for _id, title in rows:
    if not title:
        continue

    cat = classify(title)

    cur.execute(
        "UPDATE pubmed_articles SET Category_V2 = ? WHERE id = ?",
        (cat, _id)
    )
    updated += 1

conn.commit()
conn.close()

print(f"Done. Categorized {updated} articles.")
