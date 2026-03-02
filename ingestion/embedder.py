"""
Embedding Module
Generates vector embeddings using SentenceTransformers
"""
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
import structlog

logger = structlog.get_logger()


class Embedder:
    """
    Generates embeddings for text using SentenceTransformers
    Uses all-MiniLM-L6-v2 model (384 dimensions)
    """
    
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        """
        Initialize embedder
        
        Args:
            model_name: Name of the SentenceTransformer model
        """
        self.model_name = model_name
        logger.info("Loading embedding model", model=model_name)
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info("Embedding model loaded", dimension=self.embedding_dim)
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            Normalized embedding vector
        """
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding
    
    def embed_batch(self, texts: List[str], batch_size: int = 32, show_progress: bool = True) -> np.ndarray:
        """
        Generate embeddings for multiple texts in batches
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            show_progress: Show progress bar
            
        Returns:
            Array of normalized embeddings (shape: [len(texts), embedding_dim])
        """
        logger.info("Generating embeddings", count=len(texts), batch_size=batch_size)
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        
        logger.info("Embeddings generated", shape=embeddings.shape)
        return embeddings
    
    def embed_chunks(self, chunks: List[Dict], text_field: str = 'text') -> tuple:
        """
        Generate embeddings for a list of chunk dictionaries
        
        Args:
            chunks: List of chunk dictionaries
            text_field: Field name containing text to embed
            
        Returns:
            Tuple of (embeddings array, chunks list)
        """
        texts = [chunk[text_field] for chunk in chunks]
        embeddings = self.embed_batch(texts)
        
        logger.info("Chunks embedded", 
                   chunks=len(chunks),
                   embedding_shape=embeddings.shape)
        
        return embeddings, chunks


if __name__ == "__main__":
    # Test the embedder
    embedder = Embedder()
    
    # Test single embedding
    text = "High-quality wireless headphones with active noise cancellation"
    embedding = embedder.embed_text(text)
    print(f"\nSingle embedding shape: {embedding.shape}")
    print(f"Sample values: {embedding[:5]}")
    
    # Test batch embedding
    texts = [
        "Comfortable running shoes under 5000",
        "Wireless headphones with noise cancellation",
        "Gaming laptop with RTX graphics card"
    ]
    embeddings = embedder.embed_batch(texts, show_progress=False)
    print(f"\nBatch embeddings shape: {embeddings.shape}")
    
    # Test similarity
    from numpy import dot
    from numpy.linalg import norm
    similarity = dot(embeddings[0], embeddings[1]) / (norm(embeddings[0]) * norm(embeddings[1]))
    print(f"Cosine similarity between first two: {similarity:.4f}")
