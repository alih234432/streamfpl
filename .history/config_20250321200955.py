
import os

# ---------------------------- CONFIG & GLOBAL VARIABLES ----------------------------
# Path to stored data
DATA_FOLDER = "data/"

# FPL API endpoint
FPL_API_BASE = "https://fantasy.premierleague.com/api/"

# OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LLM model name
LLM_MODEL = "gpt-3.5-turbo"

# FPL RULES & TERMINOLOGY are moved to fpl_rules.py