import sqlite3

DB_PATH = "data/regalert_data.sqlite"

# Expanded keyword list for semantic categorization
# Using partial matches to capture various word forms (e.g., 'diagnos' covers diagnosis, diagnostic, etc.)
KEYWORDS = {
    'AI_Adoption': ['intelligen', 'learning', 'algorithm', 'neural', 'ai ', 'automated'],
    'Genomics': ['dna', 'genomic', 'genetic', 'sequencing', 'molecular'],
    'Imaging_Devices': ['mri', 'ct scan', 'ultrasound', 'radiology', 'imaging', 'x-ray'],
    'Diagnostics': ['diagnos', 'detect', 'biomarker', 'pathology']
}

def refine_uncategorized():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # List of "Protected" categories that should NOT be overwritten (typically high-quality source tags)
    protected_categories = ('510k Clearance', 'Post_Market_Surveillance', 'Regulatory_Compliance')
    
    print("🔍 Refining classifications for non-protected records...")
    updated_total = 0

    for category, keywords in KEYWORDS.items():
        for word in keywords:
            # Update records that are not in protected categories and match keywords in Title
            query = """
                UPDATE master_data 
                SET Category_V2 = ? 
                WHERE Category_V2 NOT IN (?, ?, ?)
                AND Title LIKE ?
            """
            cur.execute(query, (category, *protected_categories, f'%{word}%'))
            updated_total += cur.rowcount
    
    conn.commit()
    conn.close()
    print(f"✅ Classification complete. {updated_total} records were reclassified.")

if __name__ == "__main__":
    refine_uncategorized()