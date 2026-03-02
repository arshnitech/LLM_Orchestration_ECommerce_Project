"""
Configuration Management
Centralized configuration for the entire system
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/config/.env')

class Config:
    """System-wide configuration"""
    
    # Paths
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / 'data'
    LOGS_DIR = BASE_DIR / 'logs'
    
    # Database
    SQLITE_DB_PATH = DATA_DIR / 'ecommerce.db'
    
    # FAISS Index
    FAISS_INDEX_PATH = DATA_DIR / 'faiss_index.bin'
    FAISS_METADATA_PATH = DATA_DIR / 'faiss_metadata.json'
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your_openai_api_key_here')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
    
    # Embeddings
    EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
    EMBEDDING_DIM = 384
    
    # Re-ranking
    RERANKER_MODEL = 'cross-encoder/ms-marco-MiniLM-L-6-v2'
    
    # Chunking
    CHUNK_SIZE = 400  # tokens
    CHUNK_OVERLAP = 50  # tokens
    
    # Retrieval
    TOP_K_RETRIEVAL = 20  # Initial retrieval
    TOP_K_RERANK = 5      # After re-ranking
    
    # Judge
    JUDGE_ENABLED = True
    JUDGE_MODEL = 'gpt-3.5-turbo'
    JUDGE_TEMPERATURE = 0.1  # More deterministic
    
    # Application
    APP_HOST = '0.0.0.0'
    APP_PORT = 8000
    DEBUG_MODE = True
    
    # Logging
    LOG_LEVEL = 'INFO'
    METRICS_DB_PATH = LOGS_DIR / 'metrics.db'
    
    @classmethod
    def ensure_dirs(cls):
        """Create necessary directories"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
