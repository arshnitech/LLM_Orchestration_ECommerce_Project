"""
Quick Database Setup Script
Populates the e-commerce database with sample products
"""
import sqlite3
import json
from pathlib import Path

# Database path
db_path = Path(__file__).parent.parent / 'data' / 'ecommerce.db'
db_path.parent.mkdir(exist_ok=True)

print(f"Setting up database at: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create categories table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT
    )
""")

# Create products table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        category_id INTEGER,
        stock_quantity INTEGER DEFAULT 0,
        image_url TEXT,
        specifications TEXT,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    )
""")

# Insert categories
categories = [
    (1, 'Footwear', 'Shoes and footwear'),
    (2, 'Electronics', 'Electronic devices and gadgets'),
    (3, 'Clothing', 'Apparel and garments'),
    (4, 'Sports', 'Sports equipment and accessories')
]

cursor.executemany("""
    INSERT OR REPLACE INTO categories (id, name, description)
    VALUES (?, ?, ?)
""", categories)

# Insert products with rich descriptions
products = [
    (1, 'Nike Air Zoom Pegasus', 
     'Premium running shoes with responsive cushioning and breathable mesh upper. Perfect for daily training and long-distance runs. Features Zoom Air units for exceptional energy return.', 
     4999, 1, 50, '/images/nike-pegasus.jpg',
     json.dumps({'Weight': '250g', 'Drop': '10mm', 'Type': 'Neutral', 'Surface': 'Road'})),
    
    (2, 'Adidas Ultraboost 22',
     'High-performance running shoes with Boost cushioning technology. Designed for comfort and speed with a flexible Primeknit upper and Continental rubber outsole.',
     5999, 1, 35, '/images/adidas-ultraboost.jpg',
     json.dumps({'Weight': '320g', 'Drop': '10mm', 'Type': 'Neutral', 'Surface': 'Road'})),
    
    (3, 'Sony WH-1000XM5 Headphones',
     'Industry-leading noise cancelling wireless headphones with premium sound quality. Features 30-hour battery life, multipoint connection, and adaptive sound control.',
     29999, 2, 25, '/images/sony-wh1000xm5.jpg',
     json.dumps({'Battery': '30 hours', 'Connectivity': 'Bluetooth 5.2', 'Noise Cancelling': 'Yes', 'Weight': '250g'})),
    
    (4, 'Apple MacBook Pro M2',
     'Powerful laptop with M2 chip, stunning Liquid Retina display, and all-day battery life. Perfect for creative professionals and developers. 13-inch model with 256GB storage.',
     129900, 2, 15, '/images/macbook-pro-m2.jpg',
     json.dumps({'Processor': 'Apple M2', 'RAM': '8GB', 'Storage': '256GB SSD', 'Display': '13.3" Retina'})),
    
    (5, 'Samsung Galaxy S23 Ultra',
     'Premium flagship smartphone with 200MP camera, S Pen support, and powerful Snapdragon processor. Features 6.8" Dynamic AMOLED display and 5000mAh battery.',
     124999, 2, 40, '/images/samsung-s23-ultra.jpg',
     json.dumps({'Display': '6.8" AMOLED', 'Camera': '200MP', 'Battery': '5000mAh', 'RAM': '12GB'})),
    
    (6, 'Logitech MX Master 3S',
     'Advanced wireless mouse with ergonomic design and ultra-fast scrolling. Features 8K DPI sensor, quiet clicks, and works on any surface including glass.',
     8995, 2, 60, '/images/logitech-mx-master.jpg',
     json.dumps({'DPI': '8000', 'Connectivity': 'Bluetooth + USB', 'Battery': '70 days', 'Buttons': '7'})),
    
    (7, 'Puma Sports T-Shirt',
     'Breathable athletic t-shirt made with DryCELL moisture-wicking fabric. Perfect for workouts and casual wear. Available in multiple colors.',
     1299, 3, 100, '/images/puma-tshirt.jpg',
     json.dumps({'Material': 'Polyester', 'Fit': 'Regular', 'Features': 'Moisture-wicking', 'Care': 'Machine wash'})),
    
    (8, 'Decathlon Fitness Yoga Mat',
     'Non-slip exercise mat with 8mm thickness for comfortable workouts. Made from eco-friendly TPE material. Includes carrying strap.',
     1499, 4, 75, '/images/yoga-mat.jpg',
     json.dumps({'Thickness': '8mm', 'Material': 'TPE', 'Size': '183x61cm', 'Weight': '1.2kg'})),
    
    (9, 'Dell Gaming Monitor 27"',
     'High-performance gaming monitor with 165Hz refresh rate and 1ms response time. Features QHD resolution and AMD FreeSync Premium support.',
     24999, 2, 20, '/images/dell-monitor.jpg',
     json.dumps({'Size': '27"', 'Resolution': '2560x1440', 'Refresh Rate': '165Hz', 'Panel': 'IPS'})),
    
    (10, 'JBL Flip 6 Bluetooth Speaker',
     'Portable waterproof speaker with powerful sound and deep bass. IP67 rated for dust and water resistance. 12-hour playtime on single charge.',
     11999, 2, 45, '/images/jbl-flip6.jpg',
     json.dumps({'Battery': '12 hours', 'Waterproof': 'IP67', 'Connectivity': 'Bluetooth 5.1', 'Power': '30W'})),
    
    (11, 'Reebok Training Shoes',
     'Versatile training shoes designed for gym workouts and cross-training. Features stable platform and flexible forefoot for dynamic movements.',
     3999, 1, 55, '/images/reebok-training.jpg',
     json.dumps({'Weight': '300g', 'Drop': '4mm', 'Type': 'Training', 'Surface': 'Indoor'})),
    
    (12, 'Boat Airdopes Earbuds',
     'True wireless earbuds with immersive sound and long battery life. Features touch controls and IPX5 water resistance. Affordable audio solution.',
     1999, 2, 150, '/images/boat-airdopes.jpg',
     json.dumps({'Battery': '5+20 hours', 'Connectivity': 'Bluetooth 5.0', 'Water Resistance': 'IPX5', 'Drivers': '10mm'})),
    
    (13, 'HP Pavilion Gaming Laptop',
     'Affordable gaming laptop with AMD Ryzen 5 processor and NVIDIA GTX 1650 graphics. Features 15.6" FHD display and 512GB SSD storage.',
     54999, 2, 12, '/images/hp-pavilion-gaming.jpg',
     json.dumps({'Processor': 'AMD Ryzen 5', 'GPU': 'GTX 1650', 'RAM': '8GB', 'Storage': '512GB SSD'})),
    
    (14, 'Asics Gel-Kayano Running Shoes',
     'Stability running shoes with GEL cushioning technology. Designed for overpronators with excellent support and comfort for long distances.',
     9999, 1, 30, '/images/asics-kayano.jpg',
     json.dumps({'Weight': '315g', 'Drop': '10mm', 'Type': 'Stability', 'Surface': 'Road'})),
    
    (15, 'Lenovo Tab P11 Tablet',
     'Versatile Android tablet with 11" 2K display and quad speakers. Perfect for entertainment and productivity. Includes stylus pen support.',
     19999, 2, 40, '/images/lenovo-tab-p11.jpg',
     json.dumps({'Display': '11" 2K', 'Processor': 'Snapdragon 662', 'RAM': '4GB', 'Storage': '128GB'}))
]

cursor.executemany("""
    INSERT OR REPLACE INTO products (id, name, description, price, category_id, stock_quantity, image_url, specifications)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", products)

conn.commit()

# Verify
cursor.execute("SELECT COUNT(*) FROM categories")
cat_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM products")
prod_count = cursor.fetchone()[0]

print(f"✓ Database setup complete!")
print(f"  Categories: {cat_count}")
print(f"  Products: {prod_count}")

conn.close()
