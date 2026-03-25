import json
from core.runner import run_agent
from core.output_manager import save_output
from prompts.loader import load_prompt


def run():
    profile = json.load(open("data/profile.json"))
    strategy = json.load(open("data/strategy.json"))

    # Rotate themes offset by 2 from linkedin so content doesn't repeat
    themes = strategy["content_themes"]
    theme = themes[(strategy["cycle_count"] + 2) % len(themes)]

    prompt = (
        load_prompt("article")
        + f"\n\nProfile:\n{json.dumps(profile, indent=2)}"
        + f"\n\nArticle theme: {theme}"
    )

    result = run_agent(prompt, max_tokens=6000)
    save_output("articles", "article", result)
    print("[ARTICLE] Article saved locally.")

    return result
