import sqlite3
import yaml
from pathlib import Path

# Connect to SQLite database
conn = sqlite3.connect('grocery_sqlite.db')
cursor = conn.cursor()

# Fetch active products
cursor.execute('SELECT id, name, sku, category FROM products WHERE status = "active"')
products = cursor.fetchall()

print(f'Total active products: {len(products)}')

# Generate class names mapping
names = {}
for idx, product in enumerate(products):
    product_id, name, sku, category = product
    # Create slug from product name
    slug = name.lower().replace(' ', '_').replace('-', '_').replace('/', '_').replace('(', '').replace(')', '').replace(',', '')
    # Ensure unique slugs
    base_slug = slug
    suffix = 1
    while slug in [v for v in names.values()]:
        slug = f"{base_slug}_{suffix}"
        suffix += 1
    names[idx] = slug
    print(f'{idx}: {slug} (Original: {name})')

# Update yolo_class_mapping in database
for idx, product in enumerate(products):
    product_id, name, sku, category = product
    cursor.execute('UPDATE products SET yolo_class_mapping = ? WHERE id = ?', (idx, product_id))

conn.commit()

# Create data.yaml structure
dataset_root = Path(r"D:\GroceryAI\dataset")
data_yaml_content = {
    'path': str(dataset_root).replace('\\', '/'),
    'train': 'images/train',
    'val': 'images/val',
    'test': 'images/test',
    'names': names,
    'nc': len(names)
}

# Write data.yaml
yaml_path = dataset_root / 'data.yaml'
with open(yaml_path, 'w', encoding='utf-8') as f:
    yaml.dump(data_yaml_content, f, sort_keys=False, allow_unicode=True)

print(f'\nGenerated data.yaml at {yaml_path}')
print(f'Number of classes: {len(names)}')
print(f'Updated yolo_class_mapping for all products')

conn.close()
