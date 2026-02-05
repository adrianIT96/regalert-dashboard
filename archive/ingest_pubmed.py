import sqlite3
import time
from datetime import datetime
from Bio import Entrez
import pandas as pd

# =========================
# CONFIGURATION
# =========================
# Provide your email to NCBI to avoid potential blocks
Entrez.email = "your_email@example.com"  

DB_PATH = "data/regalert_data.sqlite"

# Targeted research queries for the MedTech sector
QUERIES = [
    "AI medical devices",
    "software as a medical device",
    "medical AI regulation",
    "clinical trial AI",
    "medical cybersecurity",
    "GDPR medical data",
    "FDA approved AI algorithm",
    "AI approved medical algorithm",
]

# Set the historical depth for the initial sync
START_YEAR = 2022  

# =========================
# DATABASE INITIALIZATION
# =========================
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Create table if it doesn't exist - ensuring unique PMIDs to prevent duplicates
cur.execute("""
CREATE TABLE IF NOT EXISTS pubmed_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    PMID TEXT UNIQUE,
    Title TEXT,
    Source TEXT,
    Publication_Date TEXT,
    Categories TEXT
)
""")
conn.commit()

# =========================
# DATA MAINTENANCE (OPTIONAL)
# =========================
print("Clearing temporary session data...")
cur.execute("DELETE FROM pubmed_articles")
conn.commit()

# =========================
# PUBMED SEARCH ENGINE
# =========================
def search_pubmed(query, start_year):
    print(f"Executing Search: {query}")

    handle = Entrez.esearch(
        db="pubmed",
        term=query,
        retmax=300,  # Maximum results per query
        mindate=str(start_year),
        maxdate=str(datetime.now().year),
        datetype="pdat",
    )
    results = Entrez.read(handle)
    handle.close()
    return results["IdList"]

def fetch_details(id_list):
    if not id_list:
        return []

    handle = Entrez.efetch(
        db="pubmed",
        id=",".join(id_list),
        rettype="medline",
        retmode="text",
    )
    records = handle.read()
    handle.close()
    return records

# =========================
# MEDLINE PARSER
# =========================
def parse_medline(text):
    articles = []
    current = {}

    for line in text.split("\n"):
        if line.startswith("PMID-"):
            if current:
                articles.append(current)
            current = {"PMID": line.replace("PMID- ", "").strip()}
        elif line.startswith("TI  -"):
            current["Title"] = line.replace("TI  - ", "").strip()
        elif line.startswith("DP  -"):
            # DP stands for Date of Publication
            current["Date"] = line.replace("DP  - ", "").strip()

    if current:
        articles.append(current)

    return articles

# =========================
# INGESTION PIPELINE
# =========================
inserted_count = 0

for q in QUERIES:
    ids = search_pubmed(q, START_YEAR)
    print(f"Found {len(ids)} potential articles.")

    raw_data = fetch_details(ids)
    articles = parse_medline(raw_data)

    for article in articles:
        try:
            pmid = article.get("PMID")
            title = article.get("Title", "")
            date = article.get("Date", "")

            if not pmid or not title:
                continue

            cur.execute("""
                INSERT OR IGNORE INTO pubmed_articles
                (PMID, Title, Source, Publication_Date, Categories)
                VALUES (?, ?, ?, ?, ?)
            """, (
                pmid,
                title,
                "PubMed",
                date,
                "Uncategorized"
            ))

            if cur.rowcount > 0:
                inserted_count += 1

        except Exception as e:
            print(f"Inference Error: {e}")

    conn.commit()
    # Respecting NCBI API rate limits (3 requests per second for standard users)
    time.sleep(1)  

print(f"Pipeline finished. Successfully indexed {inserted_count} new research papers.")
conn.close()