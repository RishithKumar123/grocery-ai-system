import sqlite3
from datetime import datetime

# Connect to SQLite database
conn = sqlite3.connect('grocery_sqlite.db')
cursor = conn.cursor()

# Clear existing products
cursor.execute('DELETE FROM products')

# Insert actual Patanjali products
patanjali_products = [
    ('Patanjali Amla Murabba', 'PAT-AMLA-001', 'Food', 'Patanjali', '500g', 150.00),
    ('Patanjali Honey', 'PAT-HON-002', 'Food', 'Patanjali', '250g', 180.00),
    ('Patanjali Cow Ghee', 'PAT-GHE-003', 'Food', 'Patanjali', '1L', 450.00),
    ('Patanjali Dant Kanti', 'PAT-DEN-004', 'Personal Care', 'Patanjali', '100g', 45.00),
    ('Patanjali Aloe Vera Gel', 'PAT-ALO-005', 'Personal Care', 'Patanjali', '150ml', 120.00),
    ('Patanjali Wheat Atta', 'PAT-ATT-006', 'Food', 'Patanjali', '5kg', 210.00),
    ('Patanjali Rice', 'PAT-RIC-007', 'Food', 'Patanjali', '5kg', 350.00),
    ('Patanjali Moong Dal', 'PAT-MOO-008', 'Food', 'Patanjali', '1kg', 140.00),
    ('Patanjali Chana Dal', 'PAT-CHA-009', 'Food', 'Patanjali', '1kg', 95.00),
    ('Patanjali Soap', 'PAT-SOP-010', 'Personal Care', 'Patanjali', '75g', 25.00),
]

for product in patanjali_products:
    name, sku, category, brand, weight, price = product
    barcode = f"890{sku.replace('-', '')}"
    cost_price = price * 0.8  # 20% margin
    tax = price * 0.18  # 18% GST
    now = datetime.now()
    cursor.execute('''
        INSERT INTO products (name, sku, barcode, category, brand, weight, price, cost_price, tax, expiry_tracking, status, confidence_threshold, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', 0.5, ?, ?)
    ''', (name, sku, barcode, category, brand, weight, price, cost_price, tax, now, now))

conn.commit()

# Verify
cursor.execute('SELECT id, name, sku, category FROM products')
products = cursor.fetchall()
print(f'Total products: {len(products)}')
for p in products:
    print(f'{p[0]}: {p[1]} (SKU: {p[2]}, Category: {p[3]})')

conn.close()
