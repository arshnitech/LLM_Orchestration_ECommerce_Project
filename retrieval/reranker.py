"""
Re-ranking Module
Uses cross-encoder for accurate relevance scoring and re-ranking
"""
from typing import List, Dict, Tuple
from sentence_transformers import CrossEncoder
import structlog

logger = structlog.get_logger()


class Reranker:
    """
    Cross-encoder based re-ranking system
    Re-ranks initial candidates for better precision
    """
    
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """
        Initialize reranker
        
        Args:
            model_name: Name of the cross-encoder model
        """
        self.model_name = model_name
        logger.info("Loading reranker model", model=model_name)
        self.model = CrossEncoder(model_name)
        logger.info("Reranker model loaded")
    
    def rerank(self, query: str, candidates: List[Dict], top_k: int = 5) -> Tuple[List[Dict], List[float]]:
        """
        Re-rank candidates using cross-encoder
        
        Args:
            query: Search query
            candidates: List of candidate product dictionaries
            top_k: Number of top results to return
            
        Returns:
            Tuple of (reranked_candidates, scores)
        """
        if not candidates:
            logger.warning("No candidates to rerank")
            return [], []
        
        logger.info("Reranking started", 
                   query=query,
                   candidates=len(candidates),
                   top_k=top_k)
        
        # Prepare query-document pairs
        # For products, combine name and chunks
        pairs = []
        for candidate in candidates:
            # Create document text from product info
            doc_text = self._format_candidate(candidate)
            pairs.append([query, doc_text])
        
        # Get cross-encoder scores
        scores = self.model.predict(pairs)
        
        # Sort by score (descending)
        scored_candidates = list(zip(candidates, scores))
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Take top_k
        top_candidates = [c for c, s in scored_candidates[:top_k]]
        top_scores = [s for c, s in scored_candidates[:top_k]]
        
        logger.info("Reranking completed",
                   original_top_score=float(scores[0]) if len(scores) > 0 else 0,
                   reranked_top_score=float(top_scores[0]) if top_scores else 0,
                   returned=len(top_candidates))
        
        return top_candidates, top_scores
    
    def rerank_with_comparison(self, query: str, candidates: List[Dict], 
                               initial_scores: List[float], top_k: int = 5) -> Dict:
        """
        Re-rank and show before/after comparison
        
        Args:
            query: Search query
            candidates: Initial candidates
            initial_scores: Initial retrieval scores
            top_k: Number of results to return
            
        Returns:
            Dictionary with before/after rankings and analysis
        """
        # Store initial order
        before = [
            {
                'rank': i + 1,
                'product_id': c['product_id'],
                'name': c['name'],
                'score': float(initial_scores[i]) if i < len(initial_scores) else 0
            }
            for i, c in enumerate(candidates[:top_k])
        ]
        
        # Rerank
        reranked, rerank_scores = self.rerank(query, candidates, top_k)
        
        # After ranking
        after = [
            {
                'rank': i + 1,
                'product_id': c['product_id'],
                'name': c['name'],
                'score': float(rerank_scores[i]) if i < len(rerank_scores) else 0
            }
            for i, c in enumerate(reranked)
        ]
        
        # Calculate changes
        changes = []
        before_ids = [b['product_id'] for b in before]
        for i, item in enumerate(after):
            old_rank = before_ids.index(item['product_id']) + 1 if item['product_id'] in before_ids else None
            if old_rank and old_rank != i + 1:
                change = old_rank - (i + 1)
                changes.append({
                    'product_id': item['product_id'],
                    'name': item['name'],
                    'old_rank': old_rank,
                    'new_rank': i + 1,
                    'change': change
                })
        
        logger.info("Reranking comparison",
                   significant_changes=len(changes),
                   avg_change=sum(abs(c['change']) for c in changes) / len(changes) if changes else 0)
        
        return {
            'query': query,
            'before': before,
            'after': after,
            'reranked_candidates': reranked,
            'rerank_scores': rerank_scores,
            'changes': changes,
            'improvement_summary': {
                'products_reordered': len(changes),
                'biggest_promotion': max([c['change'] for c in changes]) if changes else 0,
                'biggest_demotion': min([c['change'] for c in changes]) if changes else 0
            }
        }
    
    def _format_candidate(self, candidate: Dict) -> str:
        """
        Format candidate dictionary into text for cross-encoder
        
        Args:
            candidate: Product candidate dictionary
            
        Returns:
            Formatted text
        """
        parts = []
        
        # Product name
        if candidate.get('name'):
            parts.append(candidate['name'])
        
        # Price
        if candidate.get('price'):
            parts.append(f"Price: ₹{candidate['price']}")
        
        # Category
        if candidate.get('category'):
            parts.append(f"Category: {candidate['category']}")
        
        # Chunks (aggregated text)
        if candidate.get('chunks'):
            # Take first few chunks
            chunk_text = " ".join(candidate['chunks'][:3])
            parts.append(chunk_text)
        
        return " | ".join(parts)


if __name__ == "__main__":
    # Test the reranker
    print("Testing Reranker...")
    
    # Create test candidates
    test_candidates = [
        {
            'product_id': 1,
            'name': 'Gaming Laptop',
            'price': 75000,
            'category': 'Electronics',
            'chunks': ['High-performance gaming laptop with RTX 3060 graphics card']
        },
        {
            'product_id': 2,
            'name': 'Budget Laptop',
            'price': 30000,
            'category': 'Electronics',
            'chunks': ['Affordable laptop for basic tasks and browsing']
        },
        {
            'product_id': 3,
            'name': 'Professional Laptop',
            'price': 90000,
            'category': 'Electronics',
            'chunks': ['Business-grade laptop with excellent battery life']
        }
    ]
    
    reranker = Reranker()
    
    query = "best laptop for gaming"
    initial_scores = [0.75, 0.82, 0.68]  # Simulate retrieval scores
    
    result = reranker.rerank_with_comparison(query, test_candidates, initial_scores, top_k=3)
    
    print(f"\nQuery: {query}")
    print(f"\nBefore re-ranking:")
    for item in result['before']:
        print(f"  {item['rank']}. {item['name']} (score: {item['score']:.3f})")
    
    print(f"\nAfter re-ranking:")
    for item in result['after']:
        print(f"  {item['rank']}. {item['name']} (score: {item['score']:.3f})")
    
    if result['changes']:
        print(f"\nChanges:")
        for change in result['changes']:
            direction = "↑" if change['change'] > 0 else "↓"
            print(f"  {change['name']}: {change['old_rank']} → {change['new_rank']} ({direction}{abs(change['change'])})")
