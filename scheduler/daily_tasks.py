import os
import time
import traceback
from datetime import datetime

from agents import linkedin_agent, article_agent, hn_agent, reddit_agent, outreach_agent, opportunity_agent, optimizer_agent


def safe_run(task_name: str, fn):
    print(f"\n{'='*55}")
    print(f"[START] {task_name} — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}")

    try:
        result = fn()
        preview = result[:400] + "..." if isinstance(result, str) and len(result) > 400 else result
        print(f"[DONE] {task_name}\n{preview}")
    except Exception as e:
        print(f"[ERROR] {task_name}: {e}")
        traceback.print_exc()
        os.makedirs("output/errors", exist_ok=True)
        with open(f"output/errors/{datetime.now().strftime('%Y-%m-%d')}_{task_name.replace(' ', '_')}.txt", "a") as f:
            f.write(f"{datetime.now()}: {str(e)}\n{traceback.format_exc()}\n")


def run_all_agents():
    os.makedirs("output", exist_ok=True)

    print("\n" + "="*55)
    print("  Senior Staff Engineer Growth Engine")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55)
    print("  Running all agents now...")
    print("="*55 + "\n")

    safe_run("LinkedIn Posts", linkedin_agent.run)
    time.sleep(5)
    safe_run("Technical Article", article_agent.run)
    time.sleep(5)
    safe_run("HackerNews Post", hn_agent.run)
    time.sleep(5)
    safe_run("Reddit r/forhire", reddit_agent.run)
    time.sleep(5)
    safe_run("Outreach Templates", outreach_agent.run)
    time.sleep(5)
    safe_run("Opportunity Research", opportunity_agent.run)
    time.sleep(5)
    safe_run("Strategy Optimization", optimizer_agent.run)

    print(f"\n{'='*55}")
    print(f"  All agents complete — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55 + "\n")


# Keep for --now flag compatibility
DAY_MAP = {}
start_scheduler = run_all_agents
