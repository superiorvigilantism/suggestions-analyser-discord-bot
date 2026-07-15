from dotenv import load_dotenv
from pathlib import Path
import os

# Load .env relative to this file's location
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Load environment vars
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
FORUM_CHANNEL_ID = int(os.getenv('FORUM_CHANNEL_ID'))
PRIVATE_CHANNEL_ID = int(os.getenv('PRIVATE_CHANNEL_ID'))

# Assemble data directory at project root (supposed to exist already but what if)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
DATA_DIR = os.path.join(project_root, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Assemble config filepath
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
