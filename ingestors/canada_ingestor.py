import feedparser
import sqlite3
import pandas as pd
import requests
from datetime import datetime
from .base import BaseIngestor

class CanadaIngestor(BaseIngestor):
    """
    Ingestor for Health Canada Medical Device Recalls.
    Connects to the official RSS feed to monitor post-market surveillance actions.
    """
    
    # Updated RSS URL to prevent 404 errors
    RSS_URL = "https://recalls-rappels.canada.ca/en/feed/medical-device-recalls"

    def fetch_updates(self) -> pd.DataFrame:
        """
        Fetches the latest data from the Health Canada RSS feed.
        Uses a custom User-Agent to ensure reliable connection.
        """
        print(f"Connecting to Health Canada: {self.RSS_URL}")
        
        try:
            # Standard browser headers to prevent being blocked by the server
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(self.RSS_URL, headers=headers, timeout=20)
            
            if response.status_code == 404:
                print("CRITICAL ERROR: Health Canada RSS endpoint not found (404).")
                return pd.DataFrame()
                
            feed = feedparser.parse(response.content)
        except Exception as e:
            print(f"Connection failed: {e}")
            return pd.DataFrame()

        if not feed.entries:
            print("INFO: No new records found in the Health Canada feed.")
            return pd.DataFrame()

        records = []
        for entry in feed.entries:
            try:
                # Convert the feed time structure into a standard YYYY-MM-DD format
                date = datetime(*(entry.published_parsed[:6])).strftime('%Y-%m-%d')
            except Exception:
                date = datetime.now().strftime('%Y-%m-%d')
                
            records.append({
                "Title": entry.title,
                "Source": "Health Canada",
                "Publication_Date": date,
                "Category_V2": "Post_Market_Surveillance"
            })
            
        return pd.DataFrame(records)

    def save_to_master(self, df: pd.DataFrame):
        """
        Appends new records to the master_data table and performs deduplication.
        """
        if df.empty:
            return
            
        try:
            # Append data to the SQLite database
            df.to_sql("master_data", self.conn, if_exists="append", index=False)
            
            # Deduplication: Keep only unique records based on Title and Source
            self.conn.execute("""
                DELETE FROM master_data 
                WHERE rowid NOT IN (
                    SELECT MIN(rowid) 
                    FROM master_data 
                    GROUP BY Title, Source
                )
            """)
            self.conn.commit()
            print(f"Health Canada synchronization complete: {len(df)} records processed.")
        except Exception as e:
            print(f"Database error during synchronization: {e}")

    def run(self):
        """Main execution flow for the Canada Ingestor."""
        updates_df = self.fetch_updates()
        self.save_to_master(updates_df)
        self.close()

# Standalone execution for testing purposes
if __name__ == "__main__":
    # Ensure the path points to your actual database file
    ingestor = CanadaIngestor("data/regalert_data.sqlite")
    ingestor.run()