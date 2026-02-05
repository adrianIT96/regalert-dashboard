import sqlite3

DB_PATH = "data/regalert_data.sqlite"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS regulatory_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Source TEXT,
    Title TEXT,
    Type TEXT,
    Date TEXT,
    Category TEXT,
    Risk_Level TEXT
)
""")

conn.commit()
conn.close()

print("✅ regulatory_updates table ready.")
