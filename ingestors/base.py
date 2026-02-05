from abc import ABC, abstractmethod
import sqlite3

class BaseIngestor(ABC):
    """
    Abstract Base Class for all data ingestors.
    Ensures a consistent interface and database connectivity across different sources.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Establish connection to the local SQLite database
        self.conn = sqlite3.connect(db_path)

    @abstractmethod
    def run(self):
        """
        Main entry point for the ingestor. 
        Must be implemented by each specific source (e.g., FDA, PubMed).
        """
        pass

    def close(self):
        """Safely closes the database connection."""
        try:
            self.conn.close()
        except Exception:
            # Silence errors if connection is already closed
            pass