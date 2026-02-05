import feedparser
import sqlite3
import pandas as pd
from datetime import datetime
from .base import BaseIngestor

class EMAIngestor(BaseIngestor):
    """
    Ingestor for the European Medicines Agency (EMA).
    Monitors the 'What's New' RSS feed for regulatory updates and press releases.
    """
    
    RSS_URL = "https://www.ema.europa.eu/en/whats-new.xml"

    def fetch_updates(self) -> pd.DataFrame:
        """
        Fetches updates from the EMA RSS feed and applies basic 
        keyword-based categorization.
        """
        print(f"Fetching updates from EMA RSS: {self.RSS_URL}")
        
        try:
            feed = feedparser.parse(self.RSS_URL)
        except Exception as e:
            print(f"Failed to parse EMA feed: {e}")
            return pd.DataFrame()

        if not feed.entries:
            print("INFO: No entries found in the EMA feed.")
            return pd.DataFrame()

        records = []
        for entry in feed.entries:
            title = entry.title
            
            # Basic categorization logic
            # Default to Regulatory Compliance unless keywords suggest otherwise
            category = "Reg. Compliance"
            lower_title = title.lower()
            
            if any(word in lower_title for word in ["device", "medical", "ivd", "mdr"]):
                category = "Medical_Devices"
            elif "clinical" in lower_title:
                category = "Clin. Trials"
            
            try:
                # Convert RFC 822 date format to ISO YYYY-MM-DD
                published_dt = datetime(*(entry.published_parsed[:6]))
                formatted_date = published_dt.strftime('%Y-%m-%d')
            except Exception:
                formatted_date = datetime.now().strftime('%Y-%m-%d')
            
            records.append({
                "Title": title,
                "Source": "EMA",
                "Publication_Date": formatted_date,
                "Category_V2": category
            })
            
        return pd.DataFrame(records)

    def save_to_master(self, df: pd.DataFrame):
        """
        Saves records to the database and removes duplicates 
        to maintain data integrity.
        """
        if df.empty:
            return
            
        try:
            df.to_sql("master_data", self.conn, if_exists="append", index=False)
            
            # Deduplication based on Title and Source
            self.conn.execute("""
                DELETE FROM master_data 
                WHERE rowid NOT IN (
                    SELECT MIN(rowid) 
                    FROM master_data 
                    GROUP BY Title, Source
                )
            """)
            self.conn.commit()
            print(f"EMA synchronization complete: {len(df)} records processed.")
        except Exception as e:
            print(f"Database error (EMA): {e}")

    def run(self):
        """Main execution flow for EMAIngestor."""
        df_updates = self.fetch_updates()
        self.save_to_master(df_updates)
        self.close()

if __name__ == "__main__":
    # Point this to your actual database path
    ingestor = EMAIngestor("data/regalert_data.sqlite")
    ingestor.run()