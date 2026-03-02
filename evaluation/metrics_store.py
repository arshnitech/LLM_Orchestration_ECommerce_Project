"""
Metrics Storage and Monitoring Module
Logs queries, retrieval, generation, and evaluation metrics
"""
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import structlog

logger = structlog.get_logger()


class MetricsStore:
    """
    Stores and retrieves system metrics
    Tracks queries, retrievals, evaluations, and performance
    """
    
    def __init__(self, db_path: str):
        """
        Initialize metrics store
        
        Args:
            db_path: Path to metrics SQLite database
        """
        self.db_path = db_path
        self._ensure_db()
        logger.info("MetricsStore initialized", db_path=db_path)
    
    def _ensure_db(self):
        """Create database and tables if they don't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create queries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                filters TEXT,
                retrieval_count INTEGER,
                reranked_count INTEGER,
                response_model TEXT,
                relevance_score REAL,
                faithfulness_score REAL,
                completeness_score REAL,
                helpfulness_score REAL,
                overall_score REAL,
                response_time_ms REAL,
                tokens_used INTEGER
            )
        """)
        
        # Create daily_metrics table for aggregations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_metrics (
                date TEXT PRIMARY KEY,
                total_queries INTEGER,
                avg_relevance REAL,
                avg_faithfulness REAL,
                avg_completeness REAL,
                avg_helpfulness REAL,
                avg_overall_score REAL,
                avg_response_time_ms REAL,
                total_tokens_used INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.debug("Metrics database initialized")
    
    def log_query(self,
                  query: str,
                  filters: Optional[Dict] = None,
                  retrieval_count: int = 0,
                  reranked_count: int = 0,
                  response_model: str = None,
                  evaluation_scores: Optional[Dict] = None,
                  response_time_ms: float = 0,
                  tokens_used: int = 0):
        """
        Log a query with all metrics
        
        Args:
            query: User query
            filters: Applied filters
            retrieval_count: Number of candidates retrieved
            reranked_count: Number after re-ranking
            response_model: LLM model used
            evaluation_scores: Judge scores
            response_time_ms: Total response time
            tokens_used: LLM tokens consumed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        filters_json = json.dumps(filters) if filters else None
        
        # Extract scores
        relevance = evaluation_scores.get('relevance', 0) if evaluation_scores else 0
        faithfulness = evaluation_scores.get('faithfulness', 0) if evaluation_scores else 0
        completeness = evaluation_scores.get('completeness', 0) if evaluation_scores else 0
        helpfulness = evaluation_scores.get('helpfulness', 0) if evaluation_scores else 0
        overall = evaluation_scores.get('overall_score', 0) if evaluation_scores else 0
        
        cursor.execute("""
            INSERT INTO queries (
                timestamp, query, filters, retrieval_count, reranked_count,
                response_model, relevance_score, faithfulness_score,
                completeness_score, helpfulness_score, overall_score,
                response_time_ms, tokens_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, query, filters_json, retrieval_count, reranked_count,
              response_model, relevance, faithfulness, completeness, helpfulness,
              overall, response_time_ms, tokens_used))
        
        conn.commit()
        conn.close()
        
        logger.info("Query logged",
                   query=query[:50],
                   overall_score=overall,
                   response_time_ms=response_time_ms)
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict]:
        """Get recent queries with metrics"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM queries
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        queries = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return queries
    
    def get_aggregate_metrics(self) -> Dict:
        """Get aggregate metrics across all queries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_queries,
                AVG(relevance_score) as avg_relevance,
                AVG(faithfulness_score) as avg_faithfulness,
                AVG(completeness_score) as avg_completeness,
                AVG(helpfulness_score) as avg_helpfulness,
                AVG(overall_score) as avg_overall_score,
                AVG(response_time_ms) as avg_response_time_ms,
                SUM(tokens_used) as total_tokens_used,
                MAX(overall_score) as max_overall_score,
                MIN(overall_score) as min_overall_score
            FROM queries
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'total_queries': row[0] or 0,
                'avg_relevance': round(row[1], 2) if row[1] else 0,
                'avg_faithfulness': round(row[2], 2) if row[2] else 0,
                'avg_completeness': round(row[3], 2) if row[3] else 0,
                'avg_helpfulness': round(row[4], 2) if row[4] else 0,
                'avg_overall_score': round(row[5], 2) if row[5] else 0,
                'avg_response_time_ms': round(row[6], 2) if row[6] else 0,
                'total_tokens_used': row[7] or 0,
                'max_overall_score': round(row[8], 2) if row[8] else 0,
                'min_overall_score': round(row[9], 2) if row[9] else 0
            }
        
        return {}
    
    def get_daily_trend(self, days: int = 7) -> List[Dict]:
        """Get daily aggregated metrics"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as queries,
                AVG(overall_score) as avg_score,
                AVG(response_time_ms) as avg_time
            FROM queries
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """, (days,))
        
        trend = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Round values
        for item in trend:
            if item['avg_score']:
                item['avg_score'] = round(item['avg_score'], 2)
            if item['avg_time']:
                item['avg_time'] = round(item['avg_time'], 2)
        
        return trend


if __name__ == "__main__":
    # Test metrics store
    from config import Config
    Config.ensure_dirs()
    
    store = MetricsStore(str(Config.METRICS_DB_PATH))
    
    # Log test queries
    store.log_query(
        query="comfortable running shoes",
        filters={'price_max': 5000},
        retrieval_count=20,
        reranked_count=5,
        response_model="gpt-3.5-turbo",
        evaluation_scores={
            'relevance': 4,
            'faithfulness': 5,
            'completeness': 4,
            'helpfulness': 4,
            'overall_score': 4.25
        },
        response_time_ms=1500,
        tokens_used=250
    )
    
    print("\nRecent Queries:")
    for q in store.get_recent_queries(5):
        print(f"  {q['timestamp']}: {q['query'][:30]}... (score: {q['overall_score']})")
    
    print("\nAggregate Metrics:")
    metrics = store.get_aggregate_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
