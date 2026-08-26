import sqlite3

conn = sqlite3.connect('grocery_sqlite.db')
cursor = conn.cursor()
cursor.execute('SELECT id, name, sku, category FROM products')
products = cursor.fetchall()
print(f'Total products: {len(products)}')
for p in products:
    print(f'{p[0]}: {p[1]} (SKU: {p[2]}, Category: {p[3]})')
conn.close()
