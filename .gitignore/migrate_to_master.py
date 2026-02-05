import sqlite3
import pandas as pd

DB_PATH = "data/regalert_data.sqlite"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("--- Start migrácie na Master Table ---")

    # 1. Načítanie PubMed dát
    try:
        df_pub = pd.read_sql("SELECT Title, Source, Publication_Date, Category_V2 FROM pubmed_articles", conn)
        print(f"PubMed: Načítaných {len(df_pub)} záznamov.")
    except:
        df_pub = pd.DataFrame()
        print("PubMed tabuľka nenájdená.")

    # 2. Načítanie FDA dát
    try:
        df_fda = pd.read_sql("SELECT title as Title, 'FDA' as Source, date as Publication_Date, category as Category_V2 FROM regulatory_updates", conn)
        print(f"FDA: Načítaných {len(df_fda)} záznamov.")
    except:
        df_fda = pd.DataFrame()
        print("FDA tabuľka nenájdená.")

    # 3. Spojenie a čistenie
    df_master = pd.concat([df_pub, df_fda], ignore_index=True)
    df_master = df_master.drop_duplicates(subset=['Title'])
    
    # Oprava dátumov na jednotný formát YYYY-MM-DD
    df_master["Publication_Date"] = pd.to_datetime(df_master["Publication_Date"], errors="coerce")
    # Ak je dátum starší ako 2020 (tie tvoje 1984), dáme mu rok 2024, aby nezavadzal v histórii
    mask_old = df_master["Publication_Date"].dt.year < 2020
    df_master.loc[mask_old, "Publication_Date"] = pd.Timestamp('2024-01-01')
    # Ostatné chyby (NaT) vyplníme dneškom
    df_master["Publication_Date"] = df_master["Publication_Date"].fillna(pd.Timestamp.now())
    
    # Prevod späť na string pre SQLite, aby to bolo pekné
    df_master["Publication_Date"] = df_master["Publication_Date"].dt.strftime('%Y-%m-%d')

    # 4. Uloženie do novej tabuľky master_data
    # Ak tabuľka existuje, prepíšeme ju novými vyčistenými dátami
    df_master.to_sql("master_data", conn, if_exists="replace", index=False)
    
    print(f"--- HOTOVO: Vytvorená tabuľka 'master_data' s {len(df_master)} záznamami. ---")
    conn.close()

if __name__ == "__main__":
    migrate()