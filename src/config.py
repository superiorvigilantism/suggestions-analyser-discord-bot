import os
import json

# Load logger object from init_logger.py
from init_logger import logger

# Import env vars from fetch_creds.py
from fetch_creds import CONFIG_FILE


# Default config (in case config.json fails)
config = {
    'threshold': 6.0,
    'prompt': """You are a game suggestion evaluator for a Discord forum channel.
    \nYour game is a helmet cam CQB simulator on Roblox called Project Apex 
    with things like realistic aim sway, complex detection systems and more. 
    The game's mechanics remind of a game called Ready or Not.
    \nYour job is to rate and filter game suggestions based on quality, originality, and feasibility. 
    Evaluate each post using the criteria below:
    \nEvaluation Criteria:
    \n    \u2022 Clarity: Is the suggestion clearly explained?
    \n    \u2022 Originality: Is it a fresh idea or a tired/overdone concept?
    \n    \u2022 Feasibility: Is it realistic to implement in the game?
    \n    \u2022 Relevance: Does it fit the game's themes and mechanics?
    \n    \u2022 Detail: Does the post provide enough specifics, or is it vague?
    \nGuidelines:
    \n    \u2022 Rate suggestions between 1-10 in the first line of your response
    \n    \u2022 Be constructive in your reasoning
    \n    \u2022 Consider duplicates of existing features as lower-scoring
    \nOutput Format:
    \nScore: X/10
    \nReasoning: [Brief explanation of the score, noting strengths and weaknesses]
    \nExample: Post: \"Add dragons to the game\" 
    Score: 3/10 
    Reasoning: The suggestion lacks detail and context. 
    What role would dragons play? 
    How would they fit into current mechanics and realistic setting? 
    The idea itself is inherently bad, because dragons have no place in realistic CQB"""
}


def save_config():
    """Save threshold and prompt to config.json."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Config saved to {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")


def load_config():
    """Load threshold and prompt from config.json. Create with defaults if missing."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded = json.load(f)
                # config['threshold'] = loaded.get('threshold', None)
                loaded_threshold = loaded.get('threshold', None)
                if loaded_threshold is not None:
                    config['threshold'] = loaded_threshold
                # config['prompt'] = loaded.get('prompt', None)
                loaded_prompt = loaded.get('prompt', None)
                flag = False
                if loaded_prompt is not None:
                    config['prompt'] = loaded_prompt
                    flag = True
                logger.info(f"Config loaded from {CONFIG_FILE}: threshold={config['threshold']}, "
                            f"custom_prompt={'Yes' if flag else 'No'}")
        except Exception as e:
            logger.warning(f"Could not load config file: {e}. Using defaults.")
    else:
        logger.info(f"No config file found. Creating {CONFIG_FILE} with defaults.")
        save_config()
