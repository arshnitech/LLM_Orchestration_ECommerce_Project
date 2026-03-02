"""
Prompt Builder Module
Constructs structured prompts for RAG
"""
from typing import List, Dict
import structlog

logger = structlog.get_logger()


class PromptBuilder:
    """
    Builds structured prompts for LLM generation
    Ensures grounding to retrieved context
    """
    
    def __init__(self):
        """Initialize prompt builder"""
        logger.info("PromptBuilder initialized")
    
    def build_system_prompt(self) -> str:
        """
        Build system prompt that constrains the model
        
        Returns:
            System prompt string
        """
        return """You are an expert e-commerce product recommendation assistant.

CRITICAL RULES:
1. ONLY recommend products from the provided context
2. NEVER hallucinate or mention products not in the context
3. Base ALL recommendations on the retrieved product information
4. Explain WHY each product matches the user's query
5. Consider price, features, and user requirements
6. Be helpful, concise, and accurate

Your goal is to help customers find the perfect product based on their needs."""
    
    def build_rag_prompt(self, query: str, products: List[Dict]) -> str:
        """
        Build RAG prompt with query and retrieved products
        
        Args:
            query: User's search query
            products: List of retrieved product dictionaries
            
        Returns:
            Complete prompt string
        """
        # Build context from products
        context = self._format_products_context(products)
        
        prompt = f"""User Query: "{query}"

Retrieved Products:
{context}

Task: Based ONLY on the products listed above, provide helpful recommendations that match the user's query. Explain why each recommended product is relevant to their needs. Include product names, prices, and key features.

If none of the products match well, say so honestly.

Response:"""
        
        logger.debug("RAG prompt built",
                    query_length=len(query),
                    products_count=len(products),
                    prompt_length=len(prompt))
        
        return prompt
    
    def _format_products_context(self, products: List[Dict]) -> str:
        """
        Format products into structured context
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, product in enumerate(products, 1):
            parts = [f"\n{i}. {product.get('name', 'Unknown Product')}"]
            
            if product.get('price'):
                parts.append(f"   Price: ₹{product['price']}")
            
            if product.get('category'):
                parts.append(f"   Category: {product['category']}")
            
            if product.get('stock_quantity') is not None:
                status = "In Stock" if product['stock_quantity'] > 0 else "Out of Stock"
                parts.append(f"   Availability: {status}")
            
            # Add chunk information (product descriptions)
            if product.get('chunks'):
                # Take first 2-3 chunks for context
                chunk_text = " ".join(product['chunks'][:3])
                if len(chunk_text) > 300:
                    chunk_text = chunk_text[:300] + "..."
                parts.append(f"   Description: {chunk_text}")
            
            context_parts.append("\n".join(parts))
        
        return "\n".join(context_parts)
    
    def build_judge_prompt(self, query: str, products: List[Dict], response: str) -> str:
        """
        Build evaluation prompt for LLM-as-Judge
        
        Args:
            query: Original user query
            products: Retrieved products (ground truth)
            response: LLM's generated response
            
        Returns:
            Judge evaluation prompt
        """
        product_names = [p.get('name', 'Unknown') for p in products]
        
        prompt = f"""Evaluate the quality of this e-commerce recommendation response.

User Query: "{query}"

Available Products in Context:
{', '.join(product_names)}

Generated Response:
{response}

Evaluate on these criteria (rate 1-5 for each):

1. RELEVANCE: How well does the response match the user's query intent?
2. FAITHFULNESS: Does the response only mention products from the available context? (5 = perfect grounding, 1 = hallucinations)
3. COMPLETENESS: Does the response address all aspects of the query?
4. HELPFULNESS: Is the response actionable and useful for the customer?

Provide your evaluation in this EXACT JSON format:
{{
    "relevance": <1-5>,
    "faithfulness": <1-5>,
    "completeness": <1-5>,
    "helpfulness": <1-5>,
    "overall_score": <average of above>,
    "reasoning": "<brief explanation>"
}}

JSON Response:"""
        
        return prompt


if __name__ == "__main__":
    # Test the prompt builder
    builder = PromptBuilder()
    
    # Test system prompt
    print("System Prompt:")
    print(builder.build_system_prompt())
    
    # Test RAG prompt
    test_products = [
        {
            'product_id': 1,
            'name': 'Nike Running Shoes',
            'price': 4999,
            'category': 'Footwear',
            'stock_quantity': 25,
            'chunks': ['Comfortable running shoes with excellent cushioning and breathability']
        },
        {
            'product_id': 2,
            'name': 'Adidas Sports Shoes',
            'price': 3999,
            'category': 'Footwear',
            'stock_quantity': 15,
            'chunks': ['Lightweight sports shoes perfect for running and gym workouts']
        }
    ]
    
    query = "comfortable running shoes under 5000"
    print("\n\nRAG Prompt:")
    print(builder.build_rag_prompt(query, test_products))
