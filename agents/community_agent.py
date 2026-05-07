
from core.ollama_runner import run_agent
from prompts.loader import load_prompt

def run(context):
    prompt = load_prompt("community") + "\nContext:\n" + context
    return run_agent(prompt)
