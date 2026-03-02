"""
Semantic Retriever Module
Orchestrates semantic search with metadata filtering
"""
from typing import List, Dict, Optional, Tuple
import structlog
from .vector_store import FAISSVectorStore

logger = structlog.get_logger()


class SemanticRetriever:
    """
    Semantic retrieval system with metadata filtering
    Combines vector similarity search with structured filters
    """
    
    def __init__(self, vector_store: FAISSVectorStore, embedder):
        """
        Initialize retriever
        
        Args:
            vector_store: FAISS vector store instance
            embedder: Embedder instance for query encoding
        """
        self.vector_store = vector_store
        self.embedder = embedder
        logger.info("SemanticRetriever initialized")
    
    def retrieve(self, 
                query: str,
                top_k: int = 20,
                price_min: Optional[float] = None,
                price_max: Optional[float] = None,
                category: Optional[str] = None,
                return_unique_products: bool = True) -> Tuple[List[Dict], List[float]]:
        """
        Retrieve relevant products using semantic search
        
        Args:
            query: Search query text
            top_k: Number of initial candidates to retrieve
            price_min: Minimum price filter
            price_max: Maximum price filter
            category: Category filter
            return_unique_products: If True, deduplicate by product_id
            
        Returns:
            Tuple of (candidates, scores)
        """
        logger.info("Retrieval started",
                   query=query,
                   top_k=top_k,
                   filters={'price_min': price_min, 'price_max': price_max, 'category': category})
        
        # 1. Embed query
        query_embedding = self.embedder.embed_text(query)
        
        # 2. Vector search - get more candidates for filtering
        search_k = top_k * 3  # Over-retrieve to compensate for filtering
        scores, candidates = self.vector_store.search(query_embedding, top_k=search_k)
        
        logger.debug("Initial retrieval", candidates=len(candidates))
        
        # 3. Apply metadata filters
        if price_min is not None or price_max is not None or category is not None:
            candidates_with_scores = list(zip(candidates, scores))
            filtered_candidates = self.vector_store.filter_by_metadata(
                candidates,
                price_min=price_min,
                price_max=price_max,
                category=category
            )
            
            # Get corresponding scores
            filtered_indices = [i for i, c in enumerate(candidates) if c in filtered_candidates]
            filtered_scores = [scores[i] for i in filtered_indices]
            
            candidates = filtered_candidates[:top_k]
            scores = filtered_scores[:top_k]
            
            logger.debug("After filtering", candidates=len(candidates))
        else:
            candidates = candidates[:top_k]
            scores = scores[:top_k]
        
        # 4. Optionally deduplicate to unique products
        if return_unique_products:
            unique_products = self.vector_store.get_unique_products(candidates)
            # Aggregate scores for products (take max score across chunks)
            product_scores = {}
            for candidate, score in zip(candidates, scores):
                pid = candidate['product_id']
                if pid not in product_scores or score > product_scores[pid]:
                    product_scores[pid] = score
            
            # Map scores back to unique products
            result_scores = [product_scores[p['product_id']] for p in unique_products]
            
            logger.info("Retrieval completed",
                       unique_products=len(unique_products),
                       original_chunks=len(candidates))
            
            return unique_products, result_scores
        
        logger.info("Retrieval completed", chunks=len(candidates))
        return candidates, scores
    
    def retrieve_with_details(self, query: str, **kwargs) -> Dict:
        """
        Retrieve products with detailed metadata
        
        Args:
            query: Search query
            **kwargs: Additional arguments for retrieve()
            
        Returns:
            Dictionary with candidates, scores, and metadata
        """
        candidates, scores = self.retrieve(query, **kwargs)
        
        return {
            'query': query,
            'candidates': candidates,
            'scores': scores,
            'count': len(candidates),
            'filters_applied': {
                'price_min': kwargs.get('price_min'),
                'price_max': kwargs.get('price_max'),
                'category': kwargs.get('category')
            }
        }


if __name__ == "__main__":
    # Test will be integrated with full pipeline
    print("SemanticRetriever module - Use with orchestration pipeline")
