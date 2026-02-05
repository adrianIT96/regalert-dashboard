import sqlite3
import time
from datetime import datetime
from Bio import Entrez
from .base import BaseIngestor

class PubMedIngestor(BaseIngestor):
    """
    Ingestor for PubMed (NCBI).
    Searches for academic literature related to Medical AI and Regulatory Science.
    """
    
    # It's good practice to identify yourself to NCBI
    ENTREZ_EMAIL = "your_email@example.com"
    
    SEARCH_QUERIES = [
        "AI medical devices", "software as a medical device", 
        "medical AI regulation", "clinical trial AI", 
        "medical cybersecurity", "GDPR medical data",
        "FDA approved AI algorithm", "AI approved medical algorithm"
    ]
    
    START_YEAR = 2022

    def __init__(self, db_path: str):
        super().__init__(db_path)
        Entrez.email = self.ENTREZ_EMAIL

    def fetch_and_save(self):
        """Iterates through queries, fetches PubMed IDs, and parses article details."""
        print("🚀 Starting PubMed ingestion...")
        cur = self.conn.cursor()
        total_inserted = 0

        for query in self.SEARCH_QUERIES:
            print(f"🔍 Searching PubMed: {query}")
            try:
                # 1. Search for IDs
                handle = Entrez.esearch(db="pubmed", term=query, retmax=50, mindate=str(self.START_YEAR))
                results = Entrez.read(handle)
                handle.close()
                ids = results.get("IdList", [])

                if not ids:
                    continue

                # 2. Fetch full details for those IDs
                handle = Entrez.efetch(db="pubmed", id=",".join(ids), rettype="medline", retmode="text")
                raw_text = handle.read()
                handle.close()

                # 3. Parse and Save
                current_article = {}
                for line in raw_text.split("\n"):
                    if line.startswith("PMID-"):
                        # Save previous article before starting a new one
                        if current_article.get("Title"):
                            self._insert_article(cur, current_article)
                            if cur.rowcount > 0:
                                total_inserted += 1
                        
                        current_article = {"PMID": line.replace("PMID- ", "").strip()}
                    
                    elif line.startswith("TI  -"):
                        current_article["Title"] = line.replace("TI  - ", "").strip()
                    
                    elif line.startswith("DP  -"):
                        raw_date = line.replace("DP  - ", "").strip()
                        # Clean date format: Extract year and set to YYYY-MM-DD
                        year = raw_date[:4]
                        current_article["Date"] = f"{year}-01-01"

                self.conn.commit()
                time.sleep(0.3) # Respect NCBI's rate limits
                
            except Exception as e:
                print(f"❌ Error during PubMed query '{query}': {e}")

        print(f"✅ PubMed ingestion complete. Added {total_inserted} new articles.")

    def _insert_article(self, cursor, article):
        """Helper method to handle the SQL insertion."""
        cursor.execute("""
            INSERT OR IGNORE INTO master_data (Title, Source, Publication_Date, Category_V2)
            VALUES (?, ?, ?, ?)
        """, (article["Title"], "PubMed", article.get("Date", "2026-01-01"), "Clinical_Evidence"))

    def run(self):
        """Main entry point for PubMedIngestor."""
        self.fetch_and_save()
        self.close()

if __name__ == "__main__":
    ingestor = PubMedIngestor("data/regalert_data.sqlite")
    ingestor.run()