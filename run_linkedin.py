#!/usr/bin/env python3
"""
LinkedIn Ghostwriting Agency
5-stage pipeline: Topic Intelligence → Ghostwriter → Critic → Synthesizer → Quality Gate

Usage:
    python run_linkedin.py                    # Full pipeline, Claude API
    python run_linkedin.py --backend ollama   # Local Ollama (Critic falls back to Ollama model)

Output: output/linkedin/YYYY-MM-DD_ghostwritten.md

For draft finalization (pending drafts from Paul's Lab):
    python run_agents.py --agent linkedin
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


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

from core.config import LLM_BACKEND, ANTHROPIC_API_KEY

if LLM_BACKEND == "api" and not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not set.")
    print("  Add it to .env: ANTHROPIC_API_KEY=sk-ant-...")
    sys.exit(1)

if LLM_BACKEND == "ollama":
    print("[BACKEND] Ollama")
    print("  Stages 1, 2, 4, 5: qwen3:8b")
    print("  Stage 3 (Critic):  mistral:7b")
else:
    print("[BACKEND] Claude API")
    print("  Stages 1, 2, 4, 5: claude-sonnet-4-6")
    print("  Stage 3 (Critic):  claude-opus-4-6")

print()

if __name__ == "__main__":
    from agents.linkedin_pipeline import run
    result = run()

    print("\n" + "=" * 60)
    print("FINAL POST")
    print("=" * 60 + "\n")
    print(result)
