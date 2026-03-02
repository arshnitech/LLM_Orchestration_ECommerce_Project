// Frontend JavaScript for AI-Powered E-Commerce Search

const API_BASE = '';  // Same origin

// DOM Elements
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const priceMinInput = document.getElementById('priceMin');
const priceMaxInput = document.getElementById('priceMax');
const categoryInput = document.getElementById('category');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const productsGrid = document.getElementById('productsGrid');
const llmExplanation = document.getElementById('llmExplanation');
const evaluationCard = document.getElementById('evaluationCard');
const refreshMetricsBtn = document.getElementById('refreshMetrics');
const metricsDisplay = document.getElementById('metricsDisplay');

// Event Listeners
searchBtn.addEventListener('click', handleSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSearch();
});
refreshMetricsBtn.addEventListener('click', loadMetrics);

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadMetrics();
});

// Handle Search
async function handleSearch() {
    const query = searchInput.value.trim();
    
    if (!query) {
        alert('Please enter a search query');
        return;
    }
    
    // Show loading
    loading.classList.remove('hidden');
    results.classList.add('hidden');
    
    // Prepare request
    const requestData = {
        query: query,
        price_min: priceMinInput.value ? parseFloat(priceMinInput.value) : null,
        price_max: priceMaxInput.value ? parseFloat(priceMaxInput.value) : null,
        category: categoryInput.value || null,
        top_k: 5
    };
    
    try {
        const response = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`Search failed: ${response.statusText}`);
        }
        
        const data = await response.json();
        displayResults(data);
        
    } catch (error) {
        console.error('Search error:', error);
        alert(`Search failed: ${error.message}`);
    } finally {
        loading.classList.add('hidden');
    }
}

// Display Results
function displayResults(data) {
    // Show results section
    results.classList.remove('hidden');
    
    // Update metadata
    document.getElementById('retrievalCount').textContent = data.metadata.retrieval_count;
    document.getElementById('rerankedCount').textContent = data.metadata.reranked_count;
    document.getElementById('responseTime').textContent = `${data.metadata.response_time_ms.toFixed(0)}ms`;
    
    // Display LLM explanation
    llmExplanation.textContent = data.llm_explanation;
    
    // Display evaluation scores if available
    if (data.evaluation_score) {
        evaluationCard.classList.remove('hidden');
        const scores = data.evaluation_score;
        
        document.getElementById('relevanceScore').textContent = `${scores.relevance}/5`;
        document.getElementById('faithfulnessScore').textContent = `${scores.faithfulness}/5`;
        document.getElementById('completenessScore').textContent = `${scores.completeness}/5`;
        document.getElementById('helpfulnessScore').textContent = `${scores.helpfulness}/5`;
        document.getElementById('overallScore').textContent = `${scores.overall_score.toFixed(2)}/5`;
    } else {
        evaluationCard.classList.add('hidden');
    }
    
    // Display products
    displayProducts(data.products);
    
    // Refresh metrics
    loadMetrics();
}

// Display Products
function displayProducts(products) {
    productsGrid.innerHTML = '';
    
    if (products.length === 0) {
        productsGrid.innerHTML = '<p>No products found matching your criteria.</p>';
        return;
    }
    
    products.forEach((product, index) => {
        const card = document.createElement('div');
        card.className = 'product-card';
        
        // Calculate score percentage (normalize to 0-100)
        const scorePercent = Math.min(100, product.score * 100);
        
        card.innerHTML = `
            <div class="product-rank">${index + 1}</div>
            <div class="product-name">${escapeHtml(product.name)}</div>
            <div class="product-price">₹${product.price.toLocaleString()}</div>
            <div class="product-category">${escapeHtml(product.category || 'General')}</div>
            <div class="product-score">
                <div class="score-bar">
                    <div class="score-fill" style="width: ${scorePercent}%"></div>
                </div>
                <span class="score-text">${product.score.toFixed(3)}</span>
            </div>
        `;
        
        productsGrid.appendChild(card);
    });
}

// Load Metrics
async function loadMetrics() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        
        if (!response.ok) {
            throw new Error('Failed to load metrics');
        }
        
        const stats = await response.json();
        displayMetrics(stats);
        
    } catch (error) {
        console.error('Metrics error:', error);
        metricsDisplay.innerHTML = '<p>Failed to load metrics</p>';
    }
}

// Display Metrics
function displayMetrics(stats) {
    metricsDisplay.innerHTML = `
        <div class="metric-item">
            <div class="metric-label">Products Indexed</div>
            <div class="metric-value">${stats.products_indexed || 0}</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">Total Queries</div>
            <div class="metric-value">${stats.total_queries || 0}</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">Avg Quality Score</div>
            <div class="metric-value">${(stats.avg_overall_score || 0).toFixed(2)}/5</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">Judge Enabled</div>
            <div class="metric-value">${stats.judge_enabled ? '✓' : '✗'}</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">Re-ranker Enabled</div>
            <div class="metric-value">${stats.reranker_enabled ? '✓' : '✗'}</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">Vector Chunks</div>
            <div class="metric-value">${stats.total_chunks || 0}</div>
        </div>
    `;
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Example Queries (auto-fill on click)
const exampleQueries = [
    "comfortable running shoes under 5000",
    "gaming laptop with RTX graphics",
    "wireless headphones with noise cancellation",
    "affordable smartphone with good camera"
];

// Add example queries to interface (optional enhancement)
window.addEventListener('load', () => {
    // You can add example query buttons here if desired
    console.log('AI-Powered E-Commerce Search ready!');
    console.log('Example queries:', exampleQueries);
});
