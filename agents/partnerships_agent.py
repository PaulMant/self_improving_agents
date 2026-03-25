
from core.ollama_runner import run_agent
from prompts.loader import load_prompt

MODEL = "mistral:7b"

def run(context):
    prompt = load_prompt("partnerships") + "\nContext:\n" + context
    return run_agent(prompt, MODEL)
