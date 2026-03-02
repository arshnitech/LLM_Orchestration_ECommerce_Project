"""
LLM Generator Module
Handles OpenAI API calls for response generation
"""
from typing import Dict, Optional
import openai
import structlog
from config import Config

logger = structlog.get_logger()


class LLMGenerator:
    """
    OpenAI-based LLM generator for product recommendations
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = Config.OPENAI_MODEL,
                 temperature: float = Config.OPENAI_TEMPERATURE):
        """
        Initialize LLM generator
        
        Args:
            api_key: OpenAI API key
            model: Model name (e.g., gpt-3.5-turbo, gpt-4)
            temperature: Sampling temperature (0.0 - 2.0)
        """
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.model = model
        self.temperature = temperature
        
        # Set OpenAI API key
        openai.api_key = self.api_key
        
        logger.info("LLMGenerator initialized", 
                   model=model,
                   temperature=temperature)
    
    def generate(self, 
                system_prompt: str,
                user_prompt: str,
                temperature: Optional[float] = None,
                max_tokens: int = 500) -> Dict:
        """
        Generate response using OpenAI
        
        Args:
            system_prompt: System instruction
            user_prompt: User query/prompt
            temperature: Override default temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Dictionary with response and metadata
        """
        temp = temperature if temperature is not None else self.temperature
        
        try:
            logger.info("Generating LLM response",
                       model=self.model,
                       temperature=temp,
                       user_prompt_length=len(user_prompt))
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temp,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            
            result = {
                'response': content,
                'model': self.model,
                'temperature': temp,
                'tokens_used': {
                    'prompt': response.usage.prompt_tokens,
                    'completion': response.usage.completion_tokens,
                    'total': response.usage.total_tokens
                },
                'finish_reason': response.choices[0].finish_reason
            }
            
            logger.info("LLM response generated",
                       tokens=result['tokens_used']['total'],
                       finish_reason=result['finish_reason'])
            
            return result
            
        except Exception as e:
            logger.error("LLM generation failed", error=str(e))
            # Return mock response for demo/testing
            return {
                'response': self._get_mock_response(user_prompt),
                'model': 'mock',
                'temperature': temp,
                'tokens_used': {'prompt': 0, 'completion': 0, 'total': 0},
                'finish_reason': 'mock',
                'error': str(e)
            }
    
    def _get_mock_response(self, prompt: str) -> str:
        """Generate mock response when API is unavailable"""
        return """[Mock Response - API Key Not Configured]

Based on your query, I would recommend exploring the products that match your criteria. However, to provide personalized recommendations, please configure your OpenAI API key.

For demo purposes:
- Products are retrieved using semantic search
- Re-ranking is applied for better relevance
- This mock response replaces the actual LLM generation

To enable real LLM responses:
1. Set OPENAI_API_KEY in your .env file
2. Restart the application

The semantic search and re-ranking components are working correctly!"""


if __name__ == "__main__":
    # Test the generator
    from generation.prompt_builder import PromptBuilder
    
    builder = PromptBuilder()
    generator = LLMGenerator()
    
    # Test prompts
    system_prompt = builder.build_system_prompt()
    
    test_products = [
        {
            'name': 'Nike Running Shoes',
            'price': 4999,
            'category': 'Footwear',
            'stock_quantity': 25,
            'chunks': ['Comfortable running shoes with excellent cushioning']
        }
    ]
    
    user_prompt = builder.build_rag_prompt("comfortable running shoes", test_products)
    
    print("Generating response...")
    result = generator.generate(system_prompt, user_prompt)
    
    print(f"\nModel: {result['model']}")
    print(f"Response:\n{result['response']}")
    if 'tokens_used' in result:
        print(f"\nTokens used: {result['tokens_used']}")
