"""
FastAPI Application
Web server with REST API endpoints for semantic search
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import structlog
import uvicorn

from config import Config
from orchestration import EcommercePipeline

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="AI-Powered E-Commerce Semantic Search",
    description="Production-grade semantic search with RAG, re-ranking, and LLM-as-Judge",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize pipeline (global instance)
pipeline: Optional[EcommercePipeline] = None


# Request/Response Models
class SearchRequest(BaseModel):
    """Search request schema"""
    query: str
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    category: Optional[str] = None
    top_k: Optional[int] = 5


class SearchResponse(BaseModel):
    """Search response schema"""
    query: str
    products: list
    llm_explanation: str
    evaluation_score: Optional[dict] = None
    metadata: dict


# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup"""
    global pipeline
    
    logger.info("Starting application")
    
    try:
        # Initialize pipeline
        pipeline = EcommercePipeline(
            judge_enabled=Config.JUDGE_ENABLED,
            rerank_enabled=True
        )
        
        # Index products
        logger.info("Indexing products...")
        pipeline.index_products()
        
        logger.info("Application started successfully")
        
    except Exception as e:
        logger.error("Startup failed", error=str(e))
        raise


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend HTML"""
    try:
        with open("templates/index.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>AI-Powered E-Commerce Search API</h1><p>API is running. Access /docs for API documentation.</p>"


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Semantic search endpoint
    
    - Retrieves relevant products using semantic search
    - Applies filters and re-ranking
    - Generates LLM explanation
    - Evaluates response quality
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        logger.info("Search request received", query=request.query)
        
        # Execute search pipeline
        result = pipeline.search(
            query=request.query,
            price_min=request.price_min,
            price_max=request.price_max,
            category=request.category,
            top_k=request.top_k or 5
        )
        
        logger.info("Search completed successfully",
                   products_returned=len(result['products']),
                   response_time=result['metadata']['response_time_ms'])
        
        return result
        
    except Exception as e:
        logger.error("Search failed", error=str(e), query=request.query)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/metrics")
async def get_metrics():
    """
    Get system metrics and monitoring data
    
    Returns:
    - Aggregate metrics (avg scores, tokens, response times)
    - Recent queries
    - Daily trends
    - Vector store statistics
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        metrics = pipeline.get_metrics()
        logger.info("Metrics retrieved")
        return metrics
        
    except Exception as e:
        logger.error("Metrics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if pipeline is None:
        return {"status": "initializing"}
    
    return {
        "status": "healthy",
        "pipeline": "ready",
        "vector_store": pipeline.vector_store.get_stats()
    }


@app.post("/toggle-judge")
async def toggle_judge(enabled: bool):
    """Toggle LLM-as-Judge evaluation"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    pipeline.toggle_judge(enabled)
    return {"judge_enabled": enabled}


@app.post("/toggle-reranker")
async def toggle_reranker(enabled: bool):
    """Toggle cross-encoder re-ranking"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    pipeline.toggle_reranker(enabled)
    return {"reranker_enabled": enabled}


@app.get("/stats")
async def get_stats():
    """Get quick statistics"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    vector_stats = pipeline.vector_store.get_stats()
    metrics = pipeline.metrics.get_aggregate_metrics()
    
    return {
        "products_indexed": vector_stats['unique_products'],
        "total_chunks": vector_stats['total_vectors'],
        "total_queries": metrics.get('total_queries', 0),
        "avg_overall_score": metrics.get('avg_overall_score', 0),
        "judge_enabled": pipeline.judge_enabled,
        "reranker_enabled": pipeline.rerank_enabled
    }


# Run with: uvicorn app:app --reload --port 8000
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=Config.APP_HOST,
        port=Config.APP_PORT,
        reload=Config.DEBUG_MODE,
        log_level=Config.LOG_LEVEL.lower()
    )
