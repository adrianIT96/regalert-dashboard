import sqlite3

DB_PATH = "data/regalert_data.sqlite"

def fix_everything():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("🧹 Čistím databázu...")

    # 1. Odstránenie duplicít (ponecháme len unikátne podľa Title)
    cursor.execute("""
        DELETE FROM pubmed_articles 
        WHERE id NOT IN (
            SELECT MIN(id) FROM pubmed_articles GROUP BY Title
        )
    """)
    print(f"✅ Duplicity odstránené. Zostalo {cursor.rowcount} unikátnych záznamov.")

    # 2. Oprava kategórií (Presunieme dáta z Category_V2 tam, kde ich dashboard hľadá)
    # Najprv skontrolujeme, či máme správne názvy
    cursor.execute("PRAGMA table_info(pubmed_articles)")
    cols = [c[1] for c in cursor.fetchall()]
    
    if 'Category_V2' in cols:
        # Ak máme Category_V2, zaistíme, aby v hlavnom stĺpci nebolo 'Uncategorized'
        cursor.execute("UPDATE pubmed_articles SET Categories = Category_V2 WHERE Category_V2 != 'Other'")
        print("✅ Kategórie preklopené do hlavného stĺpca.")

    # 3. Oprava dátumov (Odstránime tie nezmyselné 2026-12-31 ak sú v budúcnosti)
    cursor.execute("UPDATE pubmed_articles SET Publication_Date = '2025-01-01' WHERE Publication_Date > '2026-02-01'")
    
    conn.commit()
    conn.close()
    print("🚀 Hotovo. Teraz skús spustiť Dashboard.")

if __name__ == "__main__":
    fix_everything()