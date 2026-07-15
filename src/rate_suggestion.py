# Import openai API library
import openai

# load logger object from init_logger.py
from init_logger import logger

# Import config from config.py
from config import config

# Import env vars from fetch_creds.py
from fetch_creds import OPENAI_API_KEY

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)


# ============================================================================
# AI RATING FUNCTION
# ============================================================================

async def rate_suggestion(title: str, content: str) -> dict:
    """
    Send suggestion to OpenAI for rating.
    Returns: {'score': float, 'reasoning': str, 'success': bool}
    """
    try:
        system_prompt = config['prompt']
        user_message = f"Suggestion Title: \n{title}\n\nSuggestion Content:\n{content}"
        
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Parse response (expects format like "Score: 7/10\nReasoning: ...")
        response_text = response.choices[0].message.content.strip()
        lines = response_text.split('\n')
        
        score = None
        reasoning = response_text
        
        for line in lines:
            if 'score' in line.lower():
                try:
                    # Extract number from "Score: X/10" or similar
                    parts = line.split(':')
                    if len(parts) > 1:
                        num_part = parts[1].strip().split('/')[0].strip()
                        score = float(num_part)
                        break
                except (ValueError, IndexError):
                    pass
        
        if score is None:
            logger.warning(f"Could not parse score from: {response_text}")
            return {'score': None, 'reasoning': response_text, 'success': False}
        
        return {'score': score, 'reasoning': reasoning, 'success': True}
    
    except Exception as e:
        error_msg = str(e)
        if e.status_code in (401, 429):
            logger.critical(f"CRITICAL OpenAI error detected: {error_msg}")
        else:
            logger.error(f"OpenAI API error: {error_msg}")
        
        return {'score': None, 'reasoning': error_msg, 'success': False}

