"""
FAISS Vector Store Module
Manages FAISS index for fast similarity search
Supports persistence and metadata filtering
"""
import faiss
import numpy as np
import json
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import structlog

logger = structlog.get_logger()


class FAISSVectorStore:
    """
    FAISS-based vector store with metadata support
    Uses IndexFlatIP (Inner Product) for cosine similarity with normalized vectors
    """
    
    def __init__(self, dimension: int = 384):
        """
        Initialize FAISS index
        
        Args:
            dimension: Embedding dimension
        """
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product for normalized vectors
        self.metadata = []  # Store chunk metadata
        self.id_to_index = {}  # Map chunk_id to index position
        logger.info("FAISSVectorStore initialized", dimension=dimension)
    
    def add_embeddings(self, embeddings: np.ndarray, chunks: List[Dict]):
        """
        Add embeddings and metadata to the index
        
        Args:
            embeddings: Numpy array of embeddings (shape: [n, dimension])
            chunks: List of chunk dictionaries with metadata
        """
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension {embeddings.shape[1]} doesn't match index dimension {self.dimension}")
        
        # Ensure float32 for FAISS
        embeddings = embeddings.astype('float32')
        
        # Add to FAISS index
        start_idx = self.index.ntotal
        self.index.add(embeddings)
        
        # Store metadata
        for i, chunk in enumerate(chunks):
            idx = start_idx + i
            self.metadata.append(chunk)
            self.id_to_index[chunk['chunk_id']] = idx
        
        logger.info("Embeddings added", 
                   count=len(chunks),
                   total_vectors=self.index.ntotal)
    
    def search(self, query_embedding: np.ndarray, top_k: int = 20) -> Tuple[List[float], List[Dict]]:
        """
        Search for similar vectors
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            Tuple of (scores, chunks)
        """
        # Ensure correct shape and type
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        query_embedding = query_embedding.astype('float32')
        
        # Search
        scores, indices = self.index.search(query_embedding, top_k)
        
        # Get metadata for results
        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self.metadata):
                results.append(self.metadata[idx])
        
        logger.debug("Search performed", 
                    query_shape=query_embedding.shape,
                    top_k=top_k,
                    results=len(results))
        
        return scores[0].tolist(), results
    
    def filter_by_metadata(self, chunks: List[Dict], 
                          price_min: Optional[float] = None,
                          price_max: Optional[float] = None,
                          category: Optional[str] = None) -> List[Dict]:
        """
        Filter chunks by metadata criteria
        
        Args:
            chunks: List of chunk dictionaries
            price_min: Minimum price filter
            price_max: Maximum price filter
            category: Category filter
            
        Returns:
            Filtered list of chunks
        """
        filtered = []
        
        for chunk in chunks:
            # Price filter
            if price_min is not None and chunk.get('price', 0) < price_min:
                continue
            if price_max is not None and chunk.get('price', float('inf')) > price_max:
                continue
            
            # Category filter
            if category is not None and chunk.get('category', '').lower() != category.lower():
                continue
            
            filtered.append(chunk)
        
        logger.debug("Metadata filtering applied",
                    original=len(chunks),
                    filtered=len(filtered),
                    price_range=(price_min, price_max),
                    category=category)
        
        return filtered
    
    def get_unique_products(self, chunks: List[Dict]) -> List[Dict]:
        """
        Get unique products from chunks (deduplicate by product_id)
        Aggregates all chunks for each product
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of unique product dictionaries
        """
        product_map = {}
        
        for chunk in chunks:
            product_id = chunk['product_id']
            if product_id not in product_map:
                product_map[product_id] = {
                    'product_id': product_id,
                    'name': chunk.get('name'),
                    'price': chunk.get('price'),
                    'category': chunk.get('category'),
                    'stock_quantity': chunk.get('stock_quantity'),
                    'image_url': chunk.get('image_url'),
                    'chunks': []
                }
            product_map[product_id]['chunks'].append(chunk['text'])
        
        products = list(product_map.values())
        logger.debug("Unique products extracted",
                    chunks=len(chunks),
                    unique_products=len(products))
        
        return products
    
    def save(self, index_path: str, metadata_path: str):
        """
        Save index and metadata to disk
        
        Args:
            index_path: Path to save FAISS index
            metadata_path: Path to save metadata JSON
        """
        # Save FAISS index
        faiss.write_index(self.index, index_path)
        
        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump({
                'metadata': self.metadata,
                'id_to_index': self.id_to_index
            }, f)
        
        logger.info("Vector store saved",
                   index_path=index_path,
                   metadata_path=metadata_path,
                   vectors=self.index.ntotal)
    
    def load(self, index_path: str, metadata_path: str):
        """
        Load index and metadata from disk
        
        Args:
            index_path: Path to FAISS index file
            metadata_path: Path to metadata JSON file
        """
        if not Path(index_path).exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")
        if not Path(metadata_path).exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        
        # Load FAISS index
        self.index = faiss.read_index(index_path)
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            data = json.load(f)
            self.metadata = data['metadata']
            self.id_to_index = data['id_to_index']
        
        logger.info("Vector store loaded",
                   index_path=index_path,
                   vectors=self.index.ntotal,
                   metadata_items=len(self.metadata))
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        return {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'metadata_count': len(self.metadata),
            'unique_products': len(set(m['product_id'] for m in self.metadata))
        }


if __name__ == "__main__":
    # Test the vector store
    print("Testing FAISSVectorStore...")
    
    # Create test data
    dimension = 384
    n_vectors = 100
    
    test_embeddings = np.random.randn(n_vectors, dimension).astype('float32')
    # Normalize
    norms = np.linalg.norm(test_embeddings, axis=1, keepdims=True)
    test_embeddings = test_embeddings / norms
    
    test_chunks = [
        {
            'chunk_id': f'test_{i}',
            'product_id': i % 10,  # 10 unique products
            'text': f'Test chunk {i}',
            'price': 1000 + i * 100,
            'category': f'Category_{i % 3}',
            'name': f'Product {i % 10}'
        }
        for i in range(n_vectors)
    ]
    
    # Initialize and add
    store = FAISSVectorStore(dimension=dimension)
    store.add_embeddings(test_embeddings, test_chunks)
    
    # Search
    query = np.random.randn(dimension).astype('float32')
    query = query / np.linalg.norm(query)
    scores, results = store.search(query, top_k=5)
    
    print(f"\nSearch results (top 5):")
    for i, (score, chunk) in enumerate(zip(scores, results)):
        print(f"{i+1}. Score: {score:.4f}, Product: {chunk['name']}, Price: {chunk['price']}")
    
    # Test filtering
    filtered = store.filter_by_metadata(results, price_min=1500, price_max=3000)
    print(f"\nFiltered results (price 1500-3000): {len(filtered)}")
    
    # Test unique products
    unique = store.get_unique_products(results)
    print(f"Unique products: {len(unique)}")
    
    # Test stats
    print(f"\nStore stats: {store.get_stats()}")
