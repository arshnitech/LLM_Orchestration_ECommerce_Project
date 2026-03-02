# 🛍️ LLM Orchestration E-Commerce Project

An AI-powered semantic search system for e-commerce that leverages Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), and advanced re-ranking techniques to deliver intelligent product search results.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🌟 Features

- **Semantic Search**: Natural language understanding for product queries
- **RAG Pipeline**: Retrieval-Augmented Generation for contextual responses
- **Re-ranking**: Advanced re-ranking with cross-encoders for improved relevance
- **LLM-as-Judge**: Automated quality evaluation of search results
- **Vector Store**: FAISS-based efficient similarity search
- **REST API**: Production-ready FastAPI endpoints
- **Web Interface**: Modern, responsive UI for search interaction
- **Structured Logging**: JSON-based logging with structlog
- **Evaluation Metrics**: Comprehensive metrics tracking and analysis

## 🏗️ Architecture

```
┌─────────────────┐
│   User Query    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         Orchestration Pipeline              │
├─────────────────────────────────────────────┤
│  1. Ingestion  → Load, Chunk, Embed         │
│  2. Retrieval  → Vector Search + Rerank     │
│  3. Generation → LLM Response Synthesis     │
│  4. Evaluation → Quality Assessment         │
└─────────────────────────────────────────────┘
```

### Core Components

1. **Ingestion Layer** (`ingestion/`)
   - Document loading and parsing
   - Intelligent text chunking
   - Embedding generation with sentence-transformers

2. **Retrieval Layer** (`retrieval/`)
   - FAISS vector store for similarity search
   - Cross-encoder re-ranking for precision
   - Hybrid retrieval strategies

3. **Generation Layer** (`generation/`)
   - LLM-based response generation
   - Prompt engineering and templates
   - Context-aware answer synthesis

4. **Evaluation Layer** (`evaluation/`)
   - LLM-as-Judge quality assessment
   - Metrics collection and storage
   - Performance analytics

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- 4GB+ RAM (for embeddings and vector store)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AhmadMahi/LLM_Orchestration_ECommerce_Project.git
   cd LLM_Orchestration_ECommerce_Project
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp backend/config/.env.example backend/config/.env
   ```
   
   Edit `backend/config/.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

5. **Initialize the database** (optional)
   ```bash
   python setup_db.py
   ```

### Running the Application

1. **Start the server**
   ```bash
   python app.py
   ```
   
   Or use uvicorn directly:
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Access the web interface**
   
   Open your browser to: http://localhost:8000

3. **API Documentation**
   
   Interactive API docs available at: http://localhost:8000/docs

## 📚 Usage

### Web Interface

1. Navigate to http://localhost:8000
2. Enter a natural language query (e.g., "laptop under $1000")
3. Apply filters for price range and categories
4. View AI-powered search results with relevance scores

### API Endpoints

#### Search Products
```bash
POST /search
Content-Type: application/json

{
  "query": "wireless headphones with noise cancellation",
  "max_price": 200,
  "min_price": 50,
  "categories": ["Electronics", "Audio"]
}
```

#### Health Check
```bash
GET /health

Response:
{
  "status": "healthy",
  "pipeline_initialized": true
}
```

### Python API

```python
from orchestration import EcommercePipeline

# Initialize pipeline
pipeline = EcommercePipeline()

# Run search
results = pipeline.run(
    query="best running shoes for marathon",
    max_price=150,
    min_price=50
)

# Access results
for result in results['retrieved_products']:
    print(f"{result['title']} - ${result['price']}")
```

## 📁 Project Structure

```
LLM_Orchestration_ECommerce_Project/
├── app.py                      # FastAPI application entry point
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── setup_db.py                # Database initialization
├── README.md                   # Project documentation
├── DEMONSTRATION.md            # Demo and testing guide
├── README_SEMANTIC_SEARCH.md   # Semantic search details
│
├── ingestion/                  # Data ingestion layer
│   ├── loader.py              # Document loading
│   ├── chunker.py             # Text chunking strategies
│   └── embedder.py            # Embedding generation
│
├── retrieval/                  # Retrieval layer
│   ├── vector_store.py        # FAISS vector database
│   ├── retriever.py           # Search and retrieval
│   └── reranker.py            # Cross-encoder re-ranking
│
├── generation/                 # Generation layer
│   ├── llm_generator.py       # LLM response generation
│   └── prompt_builder.py      # Prompt templates
│
├── evaluation/                 # Evaluation layer
│   ├── judge.py               # LLM-as-Judge evaluation
│   └── metrics_store.py       # Metrics tracking
│
├── orchestration/              # Pipeline orchestration
│   └── pipeline.py            # Main RAG pipeline
│
├── static/                     # Frontend assets
│   ├── css/styles.css         # UI styling
│   └── js/app.js              # Frontend logic
│
├── templates/                  # HTML templates
│   └── index.html             # Main web interface
│
├── data/                       # Data and indices
│   ├── faiss_index.bin        # FAISS vector index
│   └── faiss_metadata.json    # Product metadata
│
└── logs/                       # Application logs
```

## 🔧 Technologies Used

- **Framework**: FastAPI, Uvicorn
- **LLM**: OpenAI GPT models
- **Embeddings**: Sentence-Transformers (all-MiniLM-L6-v2)
- **Vector Store**: FAISS (Facebook AI Similarity Search)
- **Re-ranking**: Cross-encoder models
- **Logging**: Structlog
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Testing**: Pytest, HTTPX

## 🎯 Key Features Explained

### Semantic Search
The system understands natural language queries beyond keyword matching, enabling users to search in conversational language.

### RAG Pipeline
Combines retrieval of relevant products with LLM generation to provide contextual, informative responses.

### Re-ranking
After initial retrieval, results are re-ranked using cross-encoder models for enhanced relevance.

### LLM-as-Judge
Automated evaluation system that assesses the quality of search results using LLM-based judging.

## 📊 Evaluation & Metrics

The system tracks:
- Retrieval accuracy
- Response quality scores
- Latency metrics
- User satisfaction indicators

Metrics are stored and can be analyzed for continuous improvement.

## 🧪 Testing

Run the test suite:
```bash
pytest
```

Run specific tests:
```bash
pytest tests/test_retrieval.py
```

## 📖 Documentation

- [DEMONSTRATION.md](DEMONSTRATION.md) - Comprehensive demo guide
- [README_SEMANTIC_SEARCH.md](README_SEMANTIC_SEARCH.md) - Semantic search details
- API Docs: http://localhost:8000/docs (when server is running)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Ahmad Mahi**
- GitHub: [@AhmadMahi](https://github.com/AhmadMahi)

## 🙏 Acknowledgments

- OpenAI for GPT models
- Sentence-Transformers team
- Facebook Research for FAISS
- FastAPI community

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review the DEMONSTRATION.md guide

---

**Built with ❤️ using AI and modern MLOps practices**
