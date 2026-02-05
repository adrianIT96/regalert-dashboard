import sqlite3
import os
from datetime import datetime, timedelta
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_FILE = os.path.join(DATA_DIR, "regalert_data.sqlite")

os.makedirs(DATA_DIR, exist_ok=True)

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS pubmed_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    PMID TEXT,
    Title TEXT,
    Source TEXT,
    Publication_Date TEXT,
    Categories TEXT
)
""")

# Insert test data (last 36 months)
start_date = datetime(2022, 1, 1)

records = []
for i in range(120):
    d = start_date + timedelta(days=random.randint(0, 1100))
    records.append((
        f"PMID-{i}",
        f"Test Article {i}",
        random.choice(["PubMed", "FDA", "MHRA", "Health Canada"]),
        d.strftime("%Y-%m-%d"),
        random.choice(["AI_Adoption", "Regulatory_Compliance", "Imaging_Devices"])
    ))

cursor.executemany("""
INSERT INTO pubmed_articles (PMID, Title, Source, Publication_Date, Categories)
VALUES (?, ?, ?, ?, ?)
""", records)

conn.commit()
conn.close()

print("✅ Test SQLite database created at:")
print(DB_FILE)
