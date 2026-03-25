
from core.ollama_runner import run_agent
from prompts.loader import load_prompt
import os

MODEL = "mistral:7b"

PROMPT_DIR = "prompts"

def optimize():
    base_prompt = load_prompt("optimizer")

    for file in os.listdir(PROMPT_DIR):
        if file.endswith(".md") and file != "optimizer.md":
            path = os.path.join(PROMPT_DIR, file)
            with open(path) as f:
                content = f.read()

            prompt = base_prompt + "\nPrompt:\n" + content
            improved = run_agent(prompt, MODEL)

            with open(path, "w") as f:
                f.write(improved)
