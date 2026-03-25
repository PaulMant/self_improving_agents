import json
from core.runner import run_agent
from core.output_manager import save_output
from prompts.loader import load_prompt


def run():
    profile = json.load(open("data/profile.json"))

    prompt = (
        load_prompt("hn")
        + f"\n\nProfile:\n{json.dumps(profile, indent=2)}"
    )

    result = run_agent(prompt)
    save_output("hn", "post", result)
    print("[HN] Post ready. Copy from output/hn/ and post to the monthly 'Who wants to be hired?' thread.")
    return result
