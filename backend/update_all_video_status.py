import sqlite3

conn = sqlite3.connect('grocery_sqlite.db')
cur = conn.cursor()
cur.execute("UPDATE videos SET status='Completed' WHERE status='Failed'")
conn.commit()
print(f"Updated {cur.rowcount} failed videos to Completed status in DB.")
conn.close()
