from app.core.database import SessionLocal
from app.data.models.product_model import ProductModel

db = SessionLocal()
products = db.query(ProductModel).all()
print(f'Total products: {len(products)}')
for p in products:
    print(f'{p.id}: {p.name} (SKU: {p.sku}, Category: {p.category})')
db.close()
