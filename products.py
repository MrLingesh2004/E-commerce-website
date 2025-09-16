from app import app
from models import db, Product, Category
import random

# Sample categories
category_list = [
    {"name": "Perfumes", "description": "Fragrances for all occasions"},
    {"name": "Watches", "description": "Elegant and stylish watches"},
    {"name": "Electronics", "description": "Gadgets and accessories"},
    {"name": "Clothing", "description": "Men's and Women's apparel"},
    {"name": "Footwear", "description": "Shoes for all styles"}
]

# Sample product names
product_names = [
    "Perfume Fund", "Watch By", "Smartphone Max", "T-Shirt Classic", "Running Shoes",
    "Leather Jacket", "Bluetooth Headset", "Sunglasses Elite", "Backpack Travel", "Laptop Pro"
]

def seed_categories():
    """Create categories if they don't exist."""
    for cat in category_list:
        existing = Category.query.filter_by(name=cat["name"]).first()
        if not existing:
            new_cat = Category(name=cat["name"], description=cat["description"])
            db.session.add(new_cat)
    db.session.commit()
    print("Categories seeded.")

def create_products(n=100):
    """Create n random products."""
    categories = Category.query.all()
    for i in range(n):
        category = random.choice(categories)
        name = random.choice(product_names) + f" {i+1}"
        price = round(random.uniform(500, 5000), 2)
        image = f"https://picsum.photos/seed/{i+1}/300/300"
        stock = random.randint(1, 100)
        description = f"High-quality {name} in {category.name} category."

        product = Product(
            name=name,
            price=price,
            image=image,
            stock=stock,
            description=description,
            category_id=category.id
        )
        db.session.add(product)

    db.session.commit()
    print(f"{n} products created successfully.")

if __name__ == "__main__":
    with app.app_context():
        # Optional: clear previous products if needed
        confirm = input("This will DELETE all existing products. Continue? (y/n): ")
        if confirm.lower() == "y":
            Product.query.delete()
            db.session.commit()
            print("Previous products deleted.")

        seed_categories()
        create_products(1000)  # Add 1000 products