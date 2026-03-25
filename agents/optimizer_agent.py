import json
import re
from datetime import datetime
from core.runner import run_agent
from core.config import LLM_BACKEND
from core.output_manager import get_recent_outputs
from prompts.loader import load_prompt


def run():
    strategy = json.load(open("data/strategy.json"))
    profile = json.load(open("data/profile.json"))
    recent = get_recent_outputs(days=7)

    prompt = (
        load_prompt("optimizer")
        + f"\n\nCurrent strategy:\n{json.dumps(strategy, indent=2)}"
        + f"\n\nProfile:\n{json.dumps(profile, indent=2)}"
        + f"\n\nRecent output files (last 7 days):\n{recent}"
    )

    # Use Opus with adaptive thinking for strategic reasoning (Claude only)
    model = "claude-opus-4-6" if LLM_BACKEND == "api" else None
    thinking = LLM_BACKEND == "api"
    result = run_agent(prompt, model=model, max_tokens=2048, thinking=thinking)

    # Try to extract and apply updated strategy
    try:
        json_match = re.search(r"\{.*\}", result, re.DOTALL)
        if json_match:
            updates = json.loads(json_match.group())
            # Only update known fields
            for key in ["current_positioning", "content_themes", "target_roles", "performance_notes"]:
                if key in updates:
                    strategy[key] = updates[key]
            strategy["last_updated"] = datetime.now().strftime("%Y-%m-%d")
            strategy["cycle_count"] = strategy.get("cycle_count", 0) + 1

            with open("data/strategy.json", "w") as f:
                json.dump(strategy, f, indent=2)
            print("[OPTIMIZER] Strategy updated. New cycle count:", strategy["cycle_count"])
        else:
            print("[OPTIMIZER] Could not parse JSON from response. Strategy unchanged.")
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"[OPTIMIZER] Parse error: {e}. Strategy unchanged.")

    return result
