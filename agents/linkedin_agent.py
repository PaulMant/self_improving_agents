import json
from core.runner import run_agent
from core.output_manager import save_output
from prompts.loader import load_prompt


def run():
    profile = json.load(open("data/profile.json"))
    strategy = json.load(open("data/strategy.json"))

    # Rotate content themes based on cycle count
    themes = strategy["content_themes"]
    theme = themes[strategy["cycle_count"] % len(themes)]

    prompt = (
        load_prompt("linkedin")
        + f"\n\nProfile:\n{json.dumps(profile, indent=2)}"
        + f"\n\nFocus theme for this batch: {theme}"
        + f"\n\nCurrent positioning: {strategy['current_positioning']}"
    )

    result = run_agent(prompt)
    save_output("linkedin", "posts", result)
    return result
