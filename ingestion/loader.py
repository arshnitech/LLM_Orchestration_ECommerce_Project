"""
Data Loader Module
Loads product catalog from database and prepares for processing
"""
import sqlite3
import json
from typing import List, Dict
from pathlib import Path
import structlog

logger = structlog.get_logger()


class ProductLoader:
    """Loads product data from SQLite database"""
    
    def __init__(self, db_path: str):
        """
        Initialize loader
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        logger.info("ProductLoader initialized", db_path=db_path)
    
    def load_all_products(self) -> List[Dict]:
        """
        Load all products from database
        
        Returns:
            List of product dictionaries with all fields
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return dict-like rows
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    p.id as product_id,
                    p.name,
                    p.description,
                    p.price,
                    p.stock_quantity,
                    p.image_url,
                    p.specifications,
                    c.name as category
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
            """)
            
            products = []
            for row in cursor.fetchall():
                product = dict(row)
                # Parse JSON specifications if exists
                if product.get('specifications'):
                    try:
                        product['specifications'] = json.loads(product['specifications'])
                    except json.JSONDecodeError:
                        product['specifications'] = {}
                products.append(product)
            
            logger.info("Products loaded", count=len(products))
            return products
            
        finally:
            conn.close()
    
    def load_product_by_id(self, product_id: int) -> Dict:
        """
        Load a single product by ID
        
        Args:
            product_id: Product ID
            
        Returns:
            Product dictionary
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    p.id as product_id,
                    p.name,
                    p.description,
                    p.price,
                    p.stock_quantity,
                    p.image_url,
                    p.specifications,
                    c.name as category
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.id = ?
            """, (product_id,))
            
            row = cursor.fetchone()
            if row:
                product = dict(row)
                if product.get('specifications'):
                    try:
                        product['specifications'] = json.loads(product['specifications'])
                    except json.JSONDecodeError:
                        product['specifications'] = {}
                return product
            return None
            
        finally:
            conn.close()
    
    def get_product_count(self) -> int:
        """Get total number of products"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM products")
            return cursor.fetchone()[0]
        finally:
            conn.close()


if __name__ == "__main__":
    # Test the loader
    from config import Config
    Config.ensure_dirs()
    
    loader = ProductLoader(str(Config.SQLITE_DB_PATH))
    products = loader.load_all_products()
    print(f"Loaded {len(products)} products")
    if products:
        print(f"Sample product: {products[0]}")
