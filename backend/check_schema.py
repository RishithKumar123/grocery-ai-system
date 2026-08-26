import sqlite3

conn = sqlite3.connect('grocery_sqlite.db')
cursor = conn.cursor()

# Get table schema
cursor.execute("PRAGMA table_info(products)")
columns = cursor.fetchall()

print("Products table schema:")
for col in columns:
    print(f"  {col[1]}: {col[2]} (nullable: {not col[3]}, default: {col[4]})")

conn.close()
