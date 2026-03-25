import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "")

# LLM backend: "api" (Claude) or "ollama" (local)
# Override at runtime via --backend flag or LLM_BACKEND env var
LLM_BACKEND = os.getenv("LLM_BACKEND", "api")   # "api" | "ollama"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b")

OUTPUT_DIR = "output"
DATA_DIR = "data"
PROMPTS_DIR = "prompts"
