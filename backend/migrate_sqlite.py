import sqlite3
import os

db_path = "grocery_sqlite.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check if products table exists
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if "products" in tables:
        existing_cols = [r[1] for r in cur.execute("PRAGMA table_info(products)").fetchall()]
        
        needed_cols = [
            ("siglip_embeddings", "TEXT"),
            ("clip_embeddings", "TEXT"),
            ("yolo_class_mapping", "TEXT"),
            ("ocr_reference_text", "TEXT"),
            ("ocr_keywords", "TEXT"),
            ("confidence_threshold", "FLOAT DEFAULT 0.5"),
            ("aliases", "TEXT"),
            ("reference_image_count", "INTEGER DEFAULT 0"),
            ("embedding_model_version", "VARCHAR(50) DEFAULT 'v1'")
        ]
        
        for col_name, col_type in needed_cols:
            if col_name not in existing_cols:
                print(f"Adding column {col_name} to products table...")
                cur.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}")
                
        conn.commit()
        print("SQLite products schema successfully migrated!")
    conn.close()
