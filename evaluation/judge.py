"""
LLM-as-Judge Evaluation Module
Evaluates generated responses using LLM
"""
import json
import re
from typing import Dict, List
import openai
import structlog
from config import Config

logger = structlog.get_logger()


class LLMJudge:
    """
    LLM-based evaluation system
    Uses GPT to judge response quality on multiple criteria
    """
    
    def __init__(self,
                 api_key: str = None,
                 model: str = Config.JUDGE_MODEL,
                 temperature: float = Config.JUDGE_TEMPERATURE):
        """
        Initialize judge
        
        Args:
            api_key: OpenAI API key
            model: Model for judging
            temperature: Low temperature for consistent evaluation
        """
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.model = model
        self.temperature = temperature
        
        openai.api_key = self.api_key
        
        logger.info("LLMJudge initialized",
                   model=model,
                   temperature=temperature)
    
    def evaluate(self, 
                query: str,
                products: List[Dict],
                response: str,
                judge_prompt: str) -> Dict:
        """
        Evaluate response quality
        
        Args:
            query: Original user query
            products: Retrieved products (context)
            response: Generated response to evaluate
            judge_prompt: Evaluation prompt
            
        Returns:
            Dictionary with evaluation scores and reasoning
        """
        try:
            logger.info("Starting evaluation",
                       query_length=len(query),
                       response_length=len(response),
                       products_count=len(products))
            
            # Call OpenAI for evaluation
            eval_response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert evaluator. Provide objective, consistent assessments in valid JSON format."},
                    {"role": "user", "content": judge_prompt}
                ],
                temperature=self.temperature,
                max_tokens=500
            )
            
            content = eval_response.choices[0].message.content
            
            # Parse JSON from response
            scores = self._parse_evaluation(content)
            
            # Add metadata
            scores['tokens_used'] = {
                'prompt': eval_response.usage.prompt_tokens,
                'completion': eval_response.usage.completion_tokens,
                'total': eval_response.usage.total_tokens
            }
            scores['judge_model'] = self.model
            
            logger.info("Evaluation completed",
                       overall_score=scores.get('overall_score', 0),
                       relevance=scores.get('relevance', 0),
                       faithfulness=scores.get('faithfulness', 0))
            
            return scores
            
        except Exception as e:
            logger.error("Evaluation failed", error=str(e))
            # Return mock evaluation
            return self._get_mock_evaluation(response)
    
    def _parse_evaluation(self, content: str) -> Dict:
        """
        Parse JSON evaluation from LLM response
        
        Args:
            content: LLM response content
            
        Returns:
            Parsed evaluation dictionary
        """
        try:
            # Try to find JSON in the response
            # Look for content between { and }
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                scores = json.loads(json_str)
                
                # Validate required fields
                required = ['relevance', 'faithfulness', 'completeness', 'helpfulness']
                for field in required:
                    if field not in scores:
                        scores[field] = 3  # Default middle score
                
                # Calculate overall if not present
                if 'overall_score' not in scores:
                    scores['overall_score'] = sum([
                        scores.get('relevance', 3),
                        scores.get('faithfulness', 3),
                        scores.get('completeness', 3),
                        scores.get('helpfulness', 3)
                    ]) / 4
                
                if 'reasoning' not in scores:
                    scores['reasoning'] = "Automated evaluation"
                
                logger.debug("Evaluation parsed successfully")
                return scores
            
            else:
                logger.warning("No JSON found in evaluation response")
                return self._get_default_scores()
                
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse evaluation JSON", error=str(e))
            return self._get_default_scores()
    
    def _get_default_scores(self) -> Dict:
        """Get default scores when parsing fails"""
        return {
            'relevance': 3,
            'faithfulness': 3,
            'completeness': 3,
            'helpfulness': 3,
            'overall_score': 3.0,
            'reasoning': 'Default scores - evaluation parsing failed'
        }
    
    def _get_mock_evaluation(self, response: str) -> Dict:
        """Generate mock evaluation when API is unavailable"""
        # Simple heuristic evaluation
        length_score = min(5, len(response) / 100)  # Longer responses score higher
        has_price = 5 if '₹' in response or 'price' in response.lower() else 3
        has_product = 5 if any(word in response.lower() for word in ['product', 'recommend', 'shoes', 'laptop']) else 3
        
        scores = {
            'relevance': int(has_product),
            'faithfulness': int(has_price),
            'completeness': int(length_score) + 2,
            'helpfulness': int((has_product + has_price) / 2),
            'overall_score': 0.0,
            'reasoning': 'Mock evaluation - API key not configured',
            'judge_model': 'mock',
            'is_mock': True
        }
        
        scores['overall_score'] = round(sum([
            scores['relevance'],
            scores['faithfulness'],
            scores['completeness'],
            scores['helpfulness']
        ]) / 4, 2)
        
        logger.info("Mock evaluation generated", overall_score=scores['overall_score'])
        return scores


if __name__ == "__main__":
    # Test the judge
    from generation.prompt_builder import PromptBuilder
    
    judge = LLMJudge()
    builder = PromptBuilder()
    
    # Test data
    query = "comfortable running shoes under 5000"
    products = [
        {'name': 'Nike Running Shoes', 'price': 4999},
        {'name': 'Adidas Sports Shoes', 'price': 3999}
    ]
    response = "I recommend the Nike Running Shoes at ₹4999 which offers excellent comfort for running."
    
    # Build judge prompt
    judge_prompt = builder.build_judge_prompt(query, products, response)
    
    print("Evaluating response...")
    scores = judge.evaluate(query, products, response, judge_prompt)
    
    print(f"\nEvaluation Scores:")
    print(f"  Relevance: {scores['relevance']}/5")
    print(f"  Faithfulness: {scores['faithfulness']}/5")
    print(f"  Completeness: {scores['completeness']}/5")
    print(f"  Helpfulness: {scores['helpfulness']}/5")
    print(f"  Overall: {scores['overall_score']:.2f}/5")
    print(f"\nReasoning: {scores.get('reasoning', 'N/A')}")
