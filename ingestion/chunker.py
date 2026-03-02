"""
Chunking Module
Implements intelligent text chunking with overlap and metadata preservation
"""
from typing import List, Dict
import structlog

logger = structlog.get_logger()


class TextChunker:
    """
    Chunks product text into overlapping segments
    Preserves metadata for each chunk
    """
    
    def __init__(self, chunk_size: int = 400, overlap: int = 50):
        """
        Initialize chunker
        
        Args:
            chunk_size: Target size of each chunk in characters (approx tokens)
            overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        logger.info("TextChunker initialized", chunk_size=chunk_size, overlap=overlap)
    
    def chunk_product(self, product: Dict) -> List[Dict]:
        """
        Chunk a single product into multiple text segments
        Each chunk maintains product metadata
        
        Args:
            product: Product dictionary
            
        Returns:
            List of chunk dictionaries with metadata
        """
        chunks = []
        
        # Collect all text fields
        texts_to_chunk = []
        
        # 1. Description
        if product.get('description'):
            texts_to_chunk.append(('description', product['description']))
        
        # 2. Specifications
        if product.get('specifications'):
            specs = product['specifications']
            if isinstance(specs, dict):
                spec_text = " | ".join([f"{k}: {v}" for k, v in specs.items()])
                texts_to_chunk.append(('specifications', spec_text))
            elif isinstance(specs, str):
                texts_to_chunk.append(('specifications', specs))
        
        # 3. Reviews (if available)
        if product.get('reviews'):
            texts_to_chunk.append(('reviews', product['reviews']))
        
        # Create chunks from each text field
        chunk_id = 0
        for field_name, text in texts_to_chunk:
            field_chunks = self._chunk_text(text)
            
            for chunk_text in field_chunks:
                chunk = {
                    'product_id': product.get('product_id'),
                    'chunk_id': f"{product.get('product_id')}_{chunk_id}",
                    'text': f"{product.get('name', '')}: {chunk_text}",  # Include product name for context
                    'source_field': field_name,
                    'price': product.get('price'),
                    'category': product.get('category'),
                    'name': product.get('name'),
                    'stock_quantity': product.get('stock_quantity'),
                    'image_url': product.get('image_url')
                }
                chunks.append(chunk)
                chunk_id += 1
        
        logger.debug("Product chunked", product_id=product.get('product_id'), chunks=len(chunks))
        return chunks
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        if not text or len(text) <= self.chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for punct in ['. ', '! ', '? ', '\n']:
                    last_punct = text[start:end].rfind(punct)
                    if last_punct != -1:
                        end = start + last_punct + len(punct)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.overlap if end < len(text) else len(text)
        
        return chunks
    
    def chunk_products(self, products: List[Dict]) -> List[Dict]:
        """
        Chunk multiple products
        
        Args:
            products: List of product dictionaries
            
        Returns:
            List of all chunks from all products
        """
        all_chunks = []
        for product in products:
            chunks = self.chunk_product(product)
            all_chunks.extend(chunks)
        
        logger.info("Products chunked", 
                   products=len(products), 
                   total_chunks=len(all_chunks),
                   avg_chunks_per_product=len(all_chunks)/len(products) if products else 0)
        
        return all_chunks


if __name__ == "__main__":
    # Test the chunker
    sample_product = {
        'product_id': 1,
        'name': 'Wireless Headphones',
        'description': 'High-quality wireless headphones with active noise cancellation. Features include 30-hour battery life, premium sound quality, and comfortable over-ear design. Perfect for music lovers and professionals.',
        'price': 4999,
        'category': 'Electronics',
        'specifications': {
            'Battery Life': '30 hours',
            'Connectivity': 'Bluetooth 5.0',
            'Noise Cancellation': 'Active',
            'Weight': '250g'
        },
        'stock_quantity': 50,
        'image_url': '/images/headphones.jpg'
    }
    
    chunker = TextChunker(chunk_size=150, overlap=25)
    chunks = chunker.chunk_product(sample_product)
    
    print(f"\nGenerated {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i+1} ({chunk['source_field']}) ---")
        print(f"Text: {chunk['text'][:100]}...")
        print(f"Metadata: price={chunk['price']}, category={chunk['category']}")
