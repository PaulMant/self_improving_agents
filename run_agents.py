#!/usr/bin/env python3
"""
Senior Staff Engineer Growth Engine
Autonomous content generation and lead pipeline for Paul Mantello.

Usage:
    python run_agents.py                         # Run all agents now (default)
    python run_agents.py --backend ollama        # Run all agents, local Ollama backend
    python run_agents.py --backend api           # Run all agents, Claude API backend (explicit)
    python run_agents.py --agent linkedin        # Run one agent (claude API)
    python run_agents.py --agent linkedin --backend ollama  # Run one agent (local Ollama)

Available agents: linkedin, article, hn, reddit, outreach, opportunity, optimizer

Backend env vars:
    LLM_BACKEND=api|ollama   (default: api)
    OLLAMA_MODEL=mistral:7b  (default, only used when backend=ollama)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# --- Parse --backend early, before any module imports config ---
def _get_arg(flag: str) -> str | None:
    args = sys.argv[1:]
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            return args[idx + 1]
    return None

backend = _get_arg("--backend")
if backend:
    if backend not in ("api", "ollama"):
        print(f"ERROR: --backend must be 'api' or 'ollama', got '{backend}'")
        sys.exit(1)
    os.environ["LLM_BACKEND"] = backend

# --- Validate prerequisites after backend is set ---
from core.config import LLM_BACKEND, ANTHROPIC_API_KEY

if LLM_BACKEND == "api" and not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not set (required for --backend api).")
    print("  1. Copy .env.example to .env")
    print("  2. Add your Anthropic API key")
    print("  3. Run again  (or use --backend ollama for local inference)")
    sys.exit(1)

print(f"[BACKEND] Using: {LLM_BACKEND.upper()}", end="")
if LLM_BACKEND == "ollama":
    from core.config import OLLAMA_MODEL
    print(f" ({OLLAMA_MODEL})")
else:
    print(" (claude-sonnet-4-6 / claude-opus-4-6)")


def run_single(name: str):
    from agents import (
        linkedin_agent, article_agent, hn_agent, reddit_agent,
        outreach_agent, opportunity_agent, optimizer_agent,
    )
    agent_map = {
        "linkedin": linkedin_agent.run,
        "article": article_agent.run,
        "hn": hn_agent.run,
        "reddit": reddit_agent.run,
        "outreach": outreach_agent.run,
        "opportunity": opportunity_agent.run,
        "optimizer": optimizer_agent.run,
    }
    if name not in agent_map:
        print(f"Unknown agent '{name}'. Available: {', '.join(agent_map.keys())}")
        sys.exit(1)
    print(f"Running agent: {name}\n")
    result = agent_map[name]()
    print("\n--- OUTPUT PREVIEW ---")
    print(result[:1000] + "..." if len(result) > 1000 else result)


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--agent" in args:
        idx = args.index("--agent")
        if idx + 1 >= len(args):
            print("Usage: python run_agents.py --agent NAME [--backend api|ollama]")
            sys.exit(1)
        run_single(args[idx + 1])

    else:
        from scheduler.daily_tasks import run_all_agents
        run_all_agents()
