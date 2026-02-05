import feedparser
import sqlite3
import pandas as pd
from datetime import datetime
from .base import BaseIngestor

class MHRAIngestor(BaseIngestor):
    """
    Ingestor for the UK Medicines and Healthcare products Regulatory Agency (MHRA).
    Monitors the official GOV.UK Atom feed for medical device alerts and guidance.
    """

    # MHRA uses Atom format for their updates
    RSS_URL = "https://www.gov.uk/government/organisations/medicines-and-healthcare-products-regulatory-agency.atom"

    def fetch_updates(self) -> pd.DataFrame:
        """
        Fetches the latest regulatory updates from the MHRA Atom feed.
        Categorizes records based on MedTech-specific keywords.
        """
        print(f"Fetching updates from MHRA: {self.RSS_URL}")
        
        try:
            feed = feedparser.parse(self.RSS_URL)
        except Exception as e:
            print(f"Error parsing MHRA feed: {e}")
            return pd.DataFrame()

        if not feed.entries:
            print("INFO: No entries found in the MHRA feed.")
            return pd.DataFrame()

        records = []
        for entry in feed.entries:
            title = entry.title
            
            # Smart categorization
            # Prioritize SaMD (Software as a Medical Device) for AI-related updates
            category = "Reg. Compliance"
            lower_title = title.lower()
            
            if any(word in lower_title for word in ["software", "ai", "digital"]):
                category = "SaMD"
            elif "device" in lower_title:
                category = "Medical_Devices"
            elif "alert" in lower_title:
                category = "Safety Alert"

            # Format the ISO date (YYYY-MM-DD)
            # entry.updated typically looks like: "2026-01-20T10:00:00Z"
            formatted_date = entry.updated[:10] if entry.updated else datetime.now().strftime('%Y-%m-%d')
            
            records.append({
                "Title": title,
                "Source": "MHRA",
                "Publication_Date": formatted_date,
                "Category_V2": category
            })
            
        return pd.DataFrame(records)

    def save_to_master(self, df: pd.DataFrame):
        """
        Saves MHRA updates to the database and handles deduplication.
        """
        if df.empty:
            return
            
        try:
            df.to_sql("master_data", self.conn, if_exists="append", index=False)
            
            # Keep only unique records based on Title and Source
            self.conn.execute("""
                DELETE FROM master_data 
                WHERE rowid NOT IN (
                    SELECT MIN(rowid) 
                    FROM master_data 
                    GROUP BY Title, Source
                )
            """)
            self.conn.commit()
            print(f"MHRA synchronization complete: {len(df)} records processed.")
        except Exception as e:
            print(f"Database error (MHRA): {e}")

    def run(self):
        """Main execution flow for MHRAIngestor."""
        df_updates = self.fetch_updates()
        self.save_to_master(df_updates)
        self.close()

if __name__ == "__main__":
    # Point this to your actual database path
    ingestor = MHRAIngestor("data/regalert_data.sqlite")
    ingestor.run()