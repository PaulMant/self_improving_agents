
from core.ollama_runner import run_agent
from prompts.loader import load_prompt

def run(task):
    prompt = load_prompt("orchestrator") + "\nTask:\n" + task
    return run_agent(prompt)
