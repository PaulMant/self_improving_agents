import schedule
import time
import threading
import traceback

from agents import (
    seo_agent,
    community_agent,
    design_agent,
    partnerships_agent,
    analytics_agent,
    prompt_optimizer,
)

# Prevent multiple agents running at the same time
running_lock = threading.Lock()


def safe_run(task_name, fn):
    """
    Runs an agent safely with logging and crash protection.
    """
    if not running_lock.acquire(blocking=False):
        print(f"[SKIP] {task_name} already running")
        return

    print(f"\n[START] {task_name}")

    try:
        result = fn()
        print(f"[RESULT] {result}")

        with open("memory/growth_log.md", "a") as f:
            f.write(f"\n\n## {task_name}\n")
            f.write(result if isinstance(result, str) else str(result))

    except Exception as e:
        print(f"[ERROR] {task_name}")
        traceback.print_exc()

        with open("memory/growth_log.md", "a") as f:
            f.write(f"\n\n## ERROR in {task_name}\n{str(e)}")

    finally:
        running_lock.release()
        print(f"[END] {task_name}")


# --- Weekly Tasks ---


def monday():
    safe_run(
        "SEO Strategy",
        lambda: seo_agent.run(
            "Find SEO keywords, landing pages and blog topics for Seedext, an AI meeting assistant SaaS."
        ),
    )


def tuesday():
    safe_run(
        "Landing Page Design",
        lambda: design_agent.run(
            "Suggest improvements for the Seedext landing page to increase SaaS conversions."
        ),
    )


def wednesday():
    safe_run(
        "Community Marketing",
        lambda: community_agent.run(
            "Generate Reddit and Hacker News posts discussing AI meeting assistants and meeting productivity."
        ),
    )


def thursday():
    safe_run(
        "Partnership Discovery",
        lambda: partnerships_agent.run(
            "Find SaaS integrations and partnership opportunities for an AI meeting assistant product."
        ),
    )


def friday():
    safe_run(
        "Growth Analytics",
        lambda: analytics_agent.run(
            "Analyze recent marketing outputs and suggest growth strategy improvements."
        ),
    )


def saturday():
    safe_run(
        "Prompt Optimization",
        lambda: prompt_optimizer.optimize() or "Prompts optimized",
    )


# --- Scheduler ---


def start_scheduler():

    print("Autonomous growth agents running...")
    print("Press CTRL+C to stop.\n")

    cycle = 1

    while True:
        print(f"\n========== GROWTH CYCLE {cycle} ==========\n")

        monday()
        time.sleep(10)

        tuesday()
        time.sleep(10)

        wednesday()
        time.sleep(10)

        thursday()
        time.sleep(10)

        friday()
        time.sleep(10)

        saturday()
        time.sleep(10)

        print("\nCycle complete. Restarting...\n")

        cycle += 1

        # pause before next full cycle
        time.sleep(60)