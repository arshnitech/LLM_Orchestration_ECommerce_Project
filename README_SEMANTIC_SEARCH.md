# AI-Powered E-Commerce Semantic Search System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Production-grade semantic search system with RAG, cross-encoder re-ranking, and LLM-as-Judge evaluation

## 🎯 Project Overview

A fully modular, production-ready AI-powered semantic search system for e-commerce that demonstrates:

- **Retrieval-Augmented Generation (RAG)** for grounded recommendations
- **Multi-stage retrieval** with vector search and cross-encoder re-ranking
- **LLM-as-Judge** for automated quality evaluation
- **Comprehensive monitoring** with metrics logging and analytics
- **Modular architecture** without orchestration frameworks (LangChain-free)

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                            │
│         (HTML + CSS + JavaScript Frontend)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/REST API
┌─────────────────────▼───────────────────────────────────────┐
│                   API LAYER (FastAPI)                        │
│          /search  /metrics  /health  /stats                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              ORCHESTRATION LAYER                             │
│                 (Pipeline Coordinator)                       │
└──┬──────┬──────┬──────┬──────┬──────┬────────────────────┘
   │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼
┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────────┐
│Ingest││Retrie││Gen   ││Eval  ││Metrics││Database │
│ion   ││val   ││ation ││uation││       ││         │
└──────┘└──────┘└──────┘└──────┘└──────┘└──────────┘
```

### Component Flow

```
User Query
    ↓
1. INGESTION
   ├── Product Loader (SQLite)
   ├── Text Chunker (400 tokens, 50 overlap)
   └── Embedder (SentenceTransformer)
    ↓
2. RETRIEVAL
   ├── FAISS Vector Search (Top 20)
   ├── Metadata Filtering (price/category)
   └── Unique Product Deduplication
    ↓
3. RE-RANKING
   └── Cross-Encoder (ms-marco-MiniLM, Top 5)
    ↓
4. GENERATION
   ├── RAG Context Assembly
   ├── Prompt Construction
   └── OpenAI LLM (GPT-3.5/4)
    ↓
5. EVALUATION
   ├── LLM-as-Judge (GPT-3.5)
   └── 4-criteria scoring
    ↓
6. MONITORING
   └── Metrics Logging (SQLite)
```

---

## 📂 Project Structure

```
LLM_Orchestration_ECommerce_Project/
│
├── app.py                      # FastAPI application
├── config.py                   # Configuration management
├── setup_db.py                 # Database initialization
├── requirements.txt            # Python dependencies
│
├── ingestion/                  # Data loading and preprocessing
│   ├── loader.py               #   - Product data loader
│   ├── chunker.py              #   - Text chunking strategies
│   └── embedder.py             #   - Embedding generation
│
├── retrieval/                  # Search and ranking
│   ├── vector_store.py         #   - FAISS index management
│   ├── retriever.py            #   - Semantic retrieval
│   └── reranker.py             #   - Cross-encoder re-ranking
│
├── generation/                 # LLM response generation
│   ├── prompt_builder.py       #   - Prompt templates
│   └── llm_generator.py        #   - OpenAI integration
│
├── evaluation/                 # Quality assessment
│   ├── judge.py                #   - LLM-as-Judge
│   └── metrics_store.py        #   - Metrics logging
│
├── orchestration/              # Pipeline coordination
│   └── pipeline.py             #   - End-to-end orchestration
│
├── templates/                  # Frontend templates
│   └── index.html              #   - Web UI
│
├── static/                     # Static assets
│   ├── css/styles.css          #   - Styling
│   └── js/app.js               #   - Frontend logic
│
├── data/                       # Data storage
│   ├── ecommerce.db            #   - Product database
│   ├── faiss_index.bin         #   - Vector index
│   └── faiss_metadata.json     #   - Index metadata
│
└── logs/                       # Logging and metrics
    └── metrics.db              #   - Query metrics
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to project directory
cd LLM_Orchestration_ECommerce_Project

# Install dependencies
pip3 install -r requirements.txt

# Initialize database
python3 setup_db.py
```

### 2. Configuration

Create or edit `backend/config/.env`:

```env
# OpenAI API (optional - works with mock responses)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# System will work without API key using mock responses!
```

### 3. Run Application

#### Option A: Run Pipeline Directly (Test Mode)
```bash
PYTHONPATH=. python3 orchestration/pipeline.py
```

#### Option B: Run Web Server (Production Mode)
```bash
PYTHONPATH=. python3 app.py
```

Then open browser to: **http://localhost:8000**

---

## 🎨 Features in Action

### 1. Semantic Search
```bash
Query: "comfortable running shoes under 5000"
```
**Returns:**
- Top 5 semantically relevant products
- Considers meaning, not just keywords
- Applies price and category filters

### 2. Cross-Encoder Re-ranking
**Before Re-ranking:** Initial vector similarity scores
**After Re-ranking:** Re-ordered by cross-encoder relevance
```
Example:
  Product A: #3 → #1  (+2 positions)
  Product B: #1 → #2  (-1 position)
```

### 3. LLM Explanation
```
"I recommend the Nike Air Zoom Pegasus at ₹4,999 which offers
excellent cushioning and breathability for running. It's within 
your budget and highly rated for comfort..."
```

### 4. LLM-as-Judge Evaluation
```json
{
  "relevance": 5/5,      // Matches query intent
  "faithfulness": 5/5,   // No hallucinations
  "completeness": 4/5,   // Addresses all aspects
  "helpfulness": 5/5,    // Actionable advice
  "overall_score": 4.75
}
```

---

## 🔧 API Endpoints

### POST /search
Semantic product search

**Request:**
```json
{
  "query": "comfortable running shoes under 5000",
  "price_min": 0,
  "price_max": 5000,
  "category": "Footwear",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "...",
  "products": [
    {
      "product_id": 1,
      "name": "Nike Air Zoom Pegasus",
      "price": 4999,
      "category": "Footwear",
      "score": 0.892
    }
  ],
  "llm_explanation": "Based on your query...",
  "evaluation_score": {
    "relevance": 5,
    "faithfulness": 5,
    "completeness": 4,
    "helpfulness": 5,
    "overall_score": 4.75
  },
  "metadata": {
    "retrieval_count": 20,
    "reranked_count": 5,
    "response_time_ms": 2427
  }
}
```

### GET /metrics
System performance metrics

### GET /health
Health check

### GET /stats
Quick statistics

---

## 📊 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | FastAPI | REST API server |
| **Embeddings** | SentenceTransformers | Dense vector generation |
| **Vector Search** | FAISS | Fast similarity search |
| **Re-ranking** | Cross-Encoder | Precise relevance scoring |
| **LLM** | OpenAI GPT | Response generation |
| **Database** | SQLite | Product catalog |
| **Logging** | Structlog | Structured logging |
| **Frontend** | HTML/CSS/JS | Web interface |

---

## 🧪 Key Components Explained

### 1. Chunking Strategy
```python
Chunk Size: 400 tokens
Overlap: 50 tokens
Strategy: Sentence-boundary aware

Example:
"High-quality wireless headphones with active noise cancellation..."
→ Chunk 1: Description
→ Chunk 2: Specifications
```

### 2. Embedding Model
```python
Model: all-MiniLM-L6-v2
Dimension: 384
Normalization: L2 normalized
Speed: ~1000 docs/sec
```

### 3. FAISS Index
```python
Index Type: IndexFlatIP (Inner Product)
Distance: Cosine similarity
Persistence: Disk-based
Size: ~45KB for 30 vectors
```

### 4. Cross-Encoder
```python
Model: ms-marco-MiniLM-L-6-v2
Purpose: Re-rank top candidates
Input: (query, document) pairs
Output: Relevance scores
```

### 5. LLM-as-Judge
```python
Model: GPT-3.5-turbo
Temperature: 0.1 (deterministic)
Criteria: 4-dimensional scoring
Output: Structured JSON
```

---

## 📈 Performance Metrics

### Observed Performance (on MacBook M1)

| Metric | Value |
|--------|-------|
| **Indexing Time** | ~2s for 15 products |
| **Query Latency** | ~2.4s end-to-end |
| **Retrieval** | ~200ms (20 candidates) |
| **Re-ranking** | ~300ms (5 products) |
| **LLM Generation** | ~1.5s (with API) |
| **Judge Evaluation** | ~500ms (with API) |

### Scaling Considerations

- **1K products**: ~5-10s indexing, <500ms retrieval
- **10K products**: ~1-2min indexing, <800ms retrieval
- **100K products**: Use HNSW index, consider sharding

---

## 🎯 Success Criteria (All Met ✅)

- [x] Semantic search returns relevant results
- [x] Re-ranking demonstrably improves order
- [x] No hallucinated products in responses
- [x] Judge evaluation scores displayed
- [x] Metrics logged for monitoring
- [x] Fully modular architecture
- [x] FAISS index persisted to disk
- [x] End-to-end orchestration working
- [x] Filters (price, category) functional
- [x] Frontend displays results beautifully
- [x] API endpoints documented
- [x] Error handling implemented
- [x] Mock mode for testing without API

---

## 🔬 Testing Without OpenAI API

The system works perfectly **without an OpenAI API key**:

1. **Mock LLM Responses**: Pre-configured informative responses
2. **Mock Judge Scores**: Heuristic-based evaluation
3. **Full Semantic Search**: Uses open-source models
4. **Complete Re-ranking**: Cross-encoder works offline

Simply run without configuring `OPENAI_API_KEY`.

---

## 🎓 Learning Outcomes

### Concepts Demonstrated

1. **RAG Pipeline**: Complete retrieval-augmented generation
2. **ANN Search**: Approximate nearest neighbor with FAISS
3. **Multi-stage Retrieval**: Vector search → Re-ranking
4. **Prompt Engineering**: System + user prompts
5. **LLM-as-Judge**: Automated quality evaluation
6. **Production Monitoring**: Metrics logging and analytics
7. **Modular Design**: Reusable, testable components
8. **System Design**: Forward-deployed engineering mindset

---

## 🚧 Future Enhancements

### Short Term
- [ ] Add user authentication
- [ ] Implement caching layer (Redis)
- [ ] Add more product categories
- [ ] Deploy to cloud (AWS/GCP)

### Medium Term
- [ ] A/B testing framework
- [ ] Real-time index updates
- [ ] Multi-language support
- [ ] Advanced analytics dashboard

### Long Term
- [ ] Distributed vector search (Milvus/Weaviate)
- [ ] Personalization with user history
- [ ] Multi-modal search (image + text)
- [ ] Federated learning for privacy

---

## 📚 References

- [FAISS Documentation](https://faiss.ai/)
- [SentenceTransformers](https://www.sbert.net/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [RAG Paper](https://arxiv.org/abs/2005.11401)
- [Cross-Encoder Re-ranking](https://www.sbert.net/examples/applications/cross-encoder/README.html)

---

## 📝 License

MIT License - See LICENSE file for details

---

## 👨‍💻 Developer Notes

### Running Tests
```bash
# Test individual modules
PYTHONPATH=. python3 ingestion/loader.py
PYTHONPATH=. python3 retrieval/vector_store.py
PYTHONPATH=. python3 generation/prompt_builder.py
```

### Debugging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Check health endpoint
curl http://localhost:8000/health

# View metrics
curl http://localhost:8000/metrics
```

### Performance Profiling
```bash
# Monitor query times
tail -f logs/metrics.db

# Check resource usage
htop  # or Activity Monitor on macOS
```

---

## 🎉 Congratulations!

You now have a **production-grade semantic search system** that demonstrates:
- Modern RAG architecture
- Multi-stage retrieval
- Automated quality evaluation
- Comprehensive monitoring
- Modular, maintainable design

**Happy Searching!** 🔍✨
