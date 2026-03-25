
from core.ollama_runner import run_agent
from prompts.loader import load_prompt

MODEL = "phi3:mini"

def run(context):
    prompt = load_prompt("design") + "\nContext:\n" + context
    return run_agent(prompt, MODEL)
