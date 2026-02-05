import os
import sys

# Ensure the root directory is in the path for clean imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ingestors.fda_ingestor import FDAIngestor
from ingestors.ema_ingestor import EMAIngestor
from ingestors.mhra_ingestor import MHRAIngestor
from ingestors.canada_ingestor import CanadaIngestor
from ingestors.pubmed_ingestor import PubMedIngestor

# Path to the shared SQLite database
DB_PATH = os.path.join("data", "regalert_data.sqlite")

def run_pipeline():
    """
    Main orchestrator for the RegAlert Data Pipeline.
    Synchronizes regulatory updates from global agencies and academic sources.
    """
    print("="*50)
    print("🚀 STARTING GLOBAL REGULATORY UPDATE PIPELINE")
    print("="*50)

    # Dictionary of ingestors to allow for easy logging
    ingestor_instances = {
        "FDA (USA)": FDAIngestor(DB_PATH),
        "EMA (Europe)": EMAIngestor(DB_PATH),
        "MHRA (UK)": MHRAIngestor(DB_PATH),
        "Health Canada": CanadaIngestor(DB_PATH),
        "PubMed (Clinical)": PubMedIngestor(DB_PATH)
    }

    stats = {"success": 0, "failed": 0}

    for name, ingestor in ingestor_instances.items():
        print(f"\n[Sourcing: {name}]")
        try:
            # Each ingestor implements the .run() method from BaseIngestor
            ingestor.run()
            stats["success"] += 1
        except Exception as e:
            print(f"❌ Error during {name} synchronization: {e}")
            stats["failed"] += 1

    print("\n" + "="*50)
    print("🏁 PIPELINE EXECUTION COMPLETE")
    print(f"✅ Successful: {stats['success']} sources")
    if stats['failed'] > 0:
        print(f"⚠️ Failed: {stats['failed']} sources (check logs above)")
    print("="*50)

if __name__ == "__main__":
    # Ensure the data directory exists before running
    if not os.path.exists("data"):
        os.makedirs("data")
        print("Created missing 'data' directory.")
        
    run_pipeline()