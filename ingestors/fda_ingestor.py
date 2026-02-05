import requests
import sqlite3
from .base import BaseIngestor

class FDAIngestor(BaseIngestor):
    """
    Ingestor for the openFDA API.
    Retrieves 510(k) medical device clearances and stores them in the master database.
    """
    
    BASE_URL = "https://api.fda.gov/device/510k.json"

    def fetch_and_save(self, limit=100, max_records=1000):
        """
        Paginates through the openFDA API and saves records directly to the database.
        """
        print(f"🔍 Fetching FDA 510(k) clearances...")
        
        cur = self.conn.cursor()
        skip = 0
        total_inserted = 0

        while skip < max_records:
            params = {
                "limit": limit, 
                "skip": skip,
                "sort": "date_received:desc"  # Ensure we get the latest data first
            }
            
            try:
                response = requests.get(self.BASE_URL, params=params, timeout=20)
                if response.status_code != 200:
                    print(f"FDA API returned status code: {response.status_code}")
                    break
                
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    break

                for item in results:
                    device_name = item.get("device_name", "Unknown Device")
                    applicant = item.get("applicant", "Unknown Applicant")
                    
                    # openFDA date format: "YYYYMMDD" -> convert to "YYYY-MM-DD"
                    raw_date = item.get("date_received", "")
                    if len(raw_date) == 8:
                        formatted_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
                    else:
                        formatted_date = "2024-01-01"
                    
                    # Create a clean title for the dashboard
                    title = f"{device_name} ({applicant})"

                    cur.execute("""
                        INSERT OR IGNORE INTO master_data (Title, Source, Publication_Date, Category_V2)
                        VALUES (?, ?, ?, ?)
                    """, (title, "FDA", formatted_date, "510k Clearance"))
                    
                    if cur.rowcount > 0:
                        total_inserted += 1

                self.conn.commit()
                skip += len(results)
                print(f"   Processed {skip} FDA records...")

            except Exception as e:
                print(f"⚠️ FDA Ingestion Error: {e}")
                break

        print(f"✅ FDA ingestion complete. Added {total_inserted} new records.")

    def run(self):
        """Main entry point for the FDA ingestor."""
        self.fetch_and_save()
        self.close()

if __name__ == "__main__":
    # Standalone execution test
    ingestor = FDAIngestor("data/regalert_data.sqlite")
    ingestor.run()