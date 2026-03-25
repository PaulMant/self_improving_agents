
import os

def load_prompt(name):
    path = os.path.join("prompts", name + ".md")
    with open(path) as f:
        return f.read()
