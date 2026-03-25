import json
from core.runner import run_agent
from core.output_manager import save_output
from prompts.loader import load_prompt


def run():
    profile = json.load(open("data/profile.json"))
    strategy = json.load(open("data/strategy.json"))

    prompt = (
        load_prompt("opportunity")
        + f"\n\nProfile:\n{json.dumps(profile, indent=2)}"
        + f"\n\nIdeal clients: {json.dumps(profile['ideal_clients'], indent=2)}"
        + f"\n\nTarget roles: {', '.join(strategy['target_roles'])}"
    )

    result = run_agent(prompt)
    save_output("opportunities", "targets", result)
    return result
