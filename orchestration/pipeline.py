"""
Main Orchestration Pipeline
Coordinates all components for end-to-end semantic search
"""
import time
from typing import Dict, Optional, List
from pathlib import Path
import structlog

from config import Config
from ingestion import ProductLoader, TextChunker, Embedder
from retrieval import FAISSVectorStore, SemanticRetriever, Reranker
from generation import PromptBuilder, LLMGenerator
from evaluation import LLMJudge, MetricsStore

logger = structlog.get_logger()


class EcommercePipeline:
    """
    End-to-end semantic search pipeline
    Orchestrates: ingestion → retrieval → re-ranking → generation → evaluation
    """
    
    def __init__(self, 
                 judge_enabled: bool = Config.JUDGE_ENABLED,
                 rerank_enabled: bool = True):
        """
        Initialize pipeline with all components
        
        Args:
            judge_enabled: Enable LLM-as-Judge evaluation
            rerank_enabled: Enable cross-encoder re-ranking
        """
        self.judge_enabled = judge_enabled
        self.rerank_enabled = rerank_enabled
        
        logger.info("Initializing EcommercePipeline",
                   judge_enabled=judge_enabled,
                   rerank_enabled=rerank_enabled)
        
        # Ensure directories exist
        Config.ensure_dirs()
        
        # Initialize components
        self.loader = ProductLoader(str(Config.SQLITE_DB_PATH))
        self.chunker = TextChunker(Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
        self.embedder = Embedder(Config.EMBEDDING_MODEL)
        self.vector_store = FAISSVectorStore(Config.EMBEDDING_DIM)
        self.retriever = SemanticRetriever(self.vector_store, self.embedder)
        
        if self.rerank_enabled:
            self.reranker = Reranker(Config.RERANKER_MODEL)
        
        self.prompt_builder = PromptBuilder()
        self.generator = LLMGenerator()
        
        if self.judge_enabled:
            self.judge = LLMJudge()
        
        self.metrics = MetricsStore(str(Config.METRICS_DB_PATH))
        
        logger.info("Pipeline initialized successfully")
    
    def index_products(self, force_reindex: bool = False):
        """
        Index all products into vector store
        
        Args:
            force_reindex: Force re-indexing even if index exists
        """
        index_exists = (Path(Config.FAISS_INDEX_PATH).exists() and 
                       Path(Config.FAISS_METADATA_PATH).exists())
        
        if index_exists and not force_reindex:
            logger.info("Loading existing index")
            self.vector_store.load(str(Config.FAISS_INDEX_PATH), 
                                  str(Config.FAISS_METADATA_PATH))
            logger.info("Index loaded", 
                       stats=self.vector_store.get_stats())
            return
        
        logger.info("Starting indexing process")
        start_time = time.time()
        
        # 1. Load products
        products = self.loader.load_all_products()
        logger.info(f"Loaded {len(products)} products")
        
        # 2. Chunk products
        chunks = self.chunker.chunk_products(products)
        logger.info(f"Generated {len(chunks)} chunks")
        
        # 3. Generate embeddings
        embeddings, chunks = self.embedder.embed_chunks(chunks)
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # 4. Add to vector store
        self.vector_store.add_embeddings(embeddings, chunks)
        
        # 5. Save index
        self.vector_store.save(str(Config.FAISS_INDEX_PATH),
                              str(Config.FAISS_METADATA_PATH))
        
        elapsed = time.time() - start_time
        logger.info("Indexing completed",
                   duration_seconds=round(elapsed, 2),
                   stats=self.vector_store.get_stats())
    
    def search(self,
               query: str,
               price_min: Optional[float] = None,
               price_max: Optional[float] = None,
               category: Optional[str] = None,
               top_k: int = Config.TOP_K_RERANK) -> Dict:
        """
        Execute complete search pipeline
        
        Args:
            query: User search query
            price_min: Minimum price filter
            price_max: Maximum price filter
            category: Category filter
            top_k: Number of final results
            
        Returns:
            Complete results dictionary
        """
        start_time = time.time()
        
        logger.info("Search started",
                   query=query,
                   filters={'price_min': price_min, 'price_max': price_max, 'category': category})
        
        # Step 1: Semantic Retrieval
        candidates, retrieval_scores = self.retriever.retrieve(
            query=query,
            top_k=Config.TOP_K_RETRIEVAL,
            price_min=price_min,
            price_max=price_max,
            category=category,
            return_unique_products=True
        )
        
        logger.info("Retrieved candidates", count=len(candidates))
        
        # Step 2: Re-ranking (optional but recommended)
        if self.rerank_enabled and len(candidates) > 0:
            rerank_comparison = self.reranker.rerank_with_comparison(
                query=query,
                candidates=candidates,
                initial_scores=retrieval_scores,
                top_k=min(top_k, len(candidates))
            )
            
            final_products = rerank_comparison['reranked_candidates']
            final_scores = rerank_comparison['rerank_scores']
            rerank_changes = rerank_comparison['changes']
            
            logger.info("Re-ranking completed",
                       reordered=len(rerank_changes))
        else:
            final_products = candidates[:top_k]
            final_scores = retrieval_scores[:top_k]
            rerank_changes = []
        
        # Step 3: Generate LLM Response
        system_prompt = self.prompt_builder.build_system_prompt()
        rag_prompt = self.prompt_builder.build_rag_prompt(query, final_products)
        
        generation_result = self.generator.generate(system_prompt, rag_prompt)
        llm_response = generation_result['response']
        
        logger.info("LLM response generated",
                   model=generation_result['model'],
                   tokens=generation_result.get('tokens_used', {}).get('total', 0))
        
        # Step 4: Evaluate with Judge (optional)
        evaluation_scores = None
        if self.judge_enabled:
            judge_prompt = self.prompt_builder.build_judge_prompt(
                query, final_products, llm_response
            )
            evaluation_scores = self.judge.evaluate(
                query, final_products, llm_response, judge_prompt
            )
            
            logger.info("Evaluation completed",
                       overall_score=evaluation_scores.get('overall_score', 0))
        
        # Calculate total time
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Step 5: Log metrics
        self.metrics.log_query(
            query=query,
            filters={'price_min': price_min, 'price_max': price_max, 'category': category},
            retrieval_count=len(candidates),
            reranked_count=len(final_products),
            response_model=generation_result['model'],
            evaluation_scores=evaluation_scores,
            response_time_ms=elapsed_ms,
            tokens_used=generation_result.get('tokens_used', {}).get('total', 0)
        )
        
        # Prepare final result
        result = {
            'query': query,
            'products': [
                {
                    'product_id': p['product_id'],
                    'name': p['name'],
                    'price': p['price'],
                    'category': p['category'],
                    'image_url': p.get('image_url'),
                    'score': float(s) if s else 0
                }
                for p, s in zip(final_products, final_scores)
            ],
            'llm_explanation': llm_response,
            'evaluation_score': evaluation_scores if self.judge_enabled else None,
            'metadata': {
                'retrieval_count': len(candidates),
                'reranked_count': len(final_products),
                'rerank_changes': len(rerank_changes),
                'response_time_ms': round(elapsed_ms, 2),
                'model': generation_result['model'],
                'tokens_used': generation_result.get('tokens_used', {})
            }
        }
        
        logger.info("Search completed",
                   products=len(final_products),
                   response_time_ms=round(elapsed_ms, 2))
        
        return result
    
    def get_metrics(self) -> Dict:
        """Get system metrics for monitoring"""
        return {
            'aggregate': self.metrics.get_aggregate_metrics(),
            'recent_queries': self.metrics.get_recent_queries(10),
            'daily_trend': self.metrics.get_daily_trend(7),
            'vector_store_stats': self.vector_store.get_stats()
        }
    
    def toggle_judge(self, enabled: bool):
        """Enable or disable judge evaluation"""
        self.judge_enabled = enabled
        logger.info("Judge toggled", enabled=enabled)
    
    def toggle_reranker(self, enabled: bool):
        """Enable or disable re-ranking"""
        self.rerank_enabled = enabled
        logger.info("Reranker toggled", enabled=enabled)


if __name__ == "__main__":
    # Test the pipeline
    print("=" * 70)
    print("AI-POWERED E-COMMERCE SEMANTIC SEARCH PIPELINE")
    print("=" * 70)
    
    # Initialize pipeline
    pipeline = EcommercePipeline(judge_enabled=True, rerank_enabled=True)
    
    # Index products
    print("\n📊 Indexing products...")
    pipeline.index_products()
    
    # Test search
    print("\n🔍 Testing search pipeline...\n")
    
    test_queries = [
        "comfortable running shoes under 5000",
        "gaming laptop with RTX graphics",
        "wireless headphones with noise cancellation"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 70)
        
        result = pipeline.search(query, top_k=3)
        
        print(f"\n✓ Found {len(result['products'])} products:")
        for i, product in enumerate(result['products'], 1):
            print(f"  {i}. {product['name']} - ₹{product['price']} (score: {product['score']:.3f})")
        
        print(f"\n💬 LLM Explanation:")
        print(f"  {result['llm_explanation'][:200]}...")
        
        if result['evaluation_score']:
            print(f"\n📊 Evaluation:")
            scores = result['evaluation_score']
            print(f"  Overall: {scores['overall_score']:.2f}/5")
            print(f"  Relevance: {scores['relevance']}/5")
            print(f"  Faithfulness: {scores['faithfulness']}/5")
        
        print(f"\n⏱️  Response time: {result['metadata']['response_time_ms']:.0f}ms")
        print("=" * 70)
    
    # Show metrics
    print("\n📈 System Metrics:")
    metrics = pipeline.get_metrics()
    agg = metrics['aggregate']
    print(f"  Total Queries: {agg['total_queries']}")
    print(f"  Avg Overall Score: {agg['avg_overall_score']:.2f}/5")
    print(f"  Avg Response Time: {agg['avg_response_time_ms']:.0f}ms")
    print(f"  Total Tokens Used: {agg['total_tokens_used']}")
