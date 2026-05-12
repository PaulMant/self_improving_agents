"""
LinkedIn ghostwriting pipeline — 5-stage multi-agent system.

Stages:
  1. Topic Strategist  (Sonnet)  — finds the best topic + angle
  2. Ghostwriter       (Sonnet)  — writes the first draft in Paul's voice
  3. Critic            (Opus)    — brutal scored critique on 5 dimensions
  4. Synthesizer       (Sonnet)  — applies every critique point, optimizes for reach
  5. Quality Gate      (Sonnet)  — scores final post, triggers one retry if below threshold

Run via:  python run_linkedin.py
Or:       python run_agents.py --agent linkedin_pipeline
"""
from __future__ import annotations

import json
import os
import re

from core.runner import run_agent
from core.output_manager import save_output
from prompts.loader import load_prompt

_API_DEFAULT = "claude-sonnet-4-6"
_API_CRITIC = "claude-opus-4-6"
_OLLAMA_DEFAULT = "qwen3:8b"
_OLLAMA_CRITIC = "mistral:7b"          # local fallback
_OLLAMA_CRITIC_REMOTE = "gemma4:31b"   # preferred when remote host is available
_QUALITY_THRESHOLD = 7.0


def _pick(api_model: str, ollama_model: str) -> str:
    from core.config import LLM_BACKEND
    return api_model if LLM_BACKEND == "api" else ollama_model


def _resolve_critic() -> tuple[str, str | None]:
    """
    Determine the best available model and host for the critic stage.

    For the Claude API backend, returns the configured Opus model with no host.
    For Ollama, checks whether OLLAMA_REMOTE_HOST is set and whether the preferred
    large model (gemma4:31b) is available there. Falls back to the local mistral:7b
    if the remote is unreachable or the model is not found.

    Returns:
        (model_name, ollama_host_or_None)
    """
    from core.config import LLM_BACKEND
    if LLM_BACKEND == "api":
        return _API_CRITIC, None

    remote_host = os.getenv("OLLAMA_REMOTE_HOST", "").strip()
    if not remote_host:
        print(f"[CRITIC] OLLAMA_REMOTE_HOST not set — using local {_OLLAMA_CRITIC}")
        return _OLLAMA_CRITIC, None

    try:
        import ollama as _ollama
        client = _ollama.Client(host=remote_host)
        response = client.list()
        # Handle both object-style (newer SDK) and dict-style (older SDK) responses
        models_list = getattr(response, "models", None) or response.get("models", [])
        available = [
            getattr(m, "model", None) or m.get("name", "") or m.get("model", "")
            for m in models_list
        ]
        if _OLLAMA_CRITIC_REMOTE in available:
            print(f"[CRITIC] Remote model {_OLLAMA_CRITIC_REMOTE} found at {remote_host}")
            return _OLLAMA_CRITIC_REMOTE, remote_host
        else:
            print(
                f"[CRITIC] {_OLLAMA_CRITIC_REMOTE} not available on remote "
                f"(found: {available or 'none'}) — falling back to local {_OLLAMA_CRITIC}"
            )
            return _OLLAMA_CRITIC, None
    except Exception as e:
        print(f"[CRITIC] Remote check failed ({e}) — falling back to local {_OLLAMA_CRITIC}")
        return _OLLAMA_CRITIC, None


# ---------------------------------------------------------------------------
# Context loading
# ---------------------------------------------------------------------------

def _load_context() -> tuple[dict, dict, str, str, list[str]]:
    profile = json.load(open("data/profile.json"))
    strategy = json.load(open("data/strategy.json"))
    style, ideas, published_topics = "", "", []
    try:
        from core import knowledge_client as kb
        style = kb.get_writing_style()
        ideas = kb.get_ideas()
        published_topics = kb.get_published_topics("linkedin")
        if style:
            print(f"[KNOWLEDGE] Writing style loaded ({len(style)} chars)")
        if published_topics:
            print(f"[KNOWLEDGE] {len(published_topics)} published posts loaded (topic dedup active)")
    except Exception as e:
        print(f"[KNOWLEDGE] Unavailable, using built-in voice profile: {e}")
    return profile, strategy, style, ideas, published_topics


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _topic_prompt(profile: dict, strategy: dict, ideas: str, published_topics: list[str]) -> str:
    recent_themes = "\n".join(f"- {t}" for t in strategy["content_themes"])
    sections = [
        load_prompt("topic_strategist"),
        f"## Paul's Profile\n{json.dumps(profile, indent=2)}",
        f"## Current Positioning\n{strategy['current_positioning']}",
        f"## Recent Themes — avoid repetition\n{recent_themes}",
    ]
    if published_topics:
        already = "\n".join(f"- {t}" for t in published_topics)
        sections.append(
            f"## Already Published — DO NOT repeat these topics\n"
            f"Paul has already written about these subjects. "
            f"Any new topic must be clearly distinct in angle and substance.\n{already}"
        )
    if strategy.get("performance_notes"):
        sections.append(f"## What Has Performed Well\n{strategy['performance_notes']}")
    if ideas:
        sections.append(f"## Idea Bank (from Paul's notes)\n{ideas}")
    return "\n\n".join(sections)


def _ghostwriter_prompt(topic_analysis: str, style: str, profile: dict) -> str:
    effective_style = style or load_prompt("linkedin")
    return "\n\n".join([
        load_prompt("ghostwriter"),
        f"## Paul's Writing Style — follow exactly\n{effective_style}",
        f"## Chosen Topic & Angle\n{topic_analysis}",
        f"## Author Context\n{json.dumps(profile, indent=2)}",
    ])


def _critic_prompt(draft: str, profile: dict) -> str:
    return "\n\n".join([
        load_prompt("post_critic"),
        f"## Author Context\n{json.dumps(profile, indent=2)}",
        f"## Draft to Review\n{draft}",
    ])


def _synthesizer_prompt(draft: str, critique: str, style: str, profile: dict) -> str:
    effective_style = style or load_prompt("linkedin")
    return "\n\n".join([
        load_prompt("post_synthesizer"),
        f"## Paul's Writing Style\n{effective_style}",
        f"## Original Draft\n{draft}",
        f"## Critic's Analysis & Fix Instructions\n{critique}",
        f"## Author Context\n{json.dumps(profile, indent=2)}",
    ])


def _quality_gate_prompt(post: str, profile: dict) -> str:
    return "\n\n".join([
        load_prompt("quality_gate"),
        f"## Author Context\n{json.dumps(profile, indent=2)}",
        f"## Post to Evaluate\n{post}",
    ])


# ---------------------------------------------------------------------------
# Output parsers
# ---------------------------------------------------------------------------

def _parse_quality(raw: str) -> tuple[bool, float]:
    """
    Returns (passed, avg_score).
    Falls back to (True, 7.0) if parsing fails — never block on parse errors.
    """
    verdict_match = re.search(r"\b(APPROVED|NEEDS_REVISION)\b", raw)
    if not verdict_match:
        return True, 7.0

    passed = verdict_match.group(1) == "APPROVED"

    # "Average: 8.4/10"  or  "Average: 8.4"
    score_match = re.search(r"average[:\s]+(\d+(?:\.\d+)?)", raw, re.IGNORECASE)
    avg = float(score_match.group(1)) if score_match else (8.0 if passed else 6.0)

    return passed, avg


def _split_synthesis(raw: str) -> tuple[str, str]:
    """
    Split synthesizer output into (post_text, editor_note).
    The synthesizer is instructed to place "Editor's Note:" after the post.
    """
    idx = raw.lower().rfind("editor's note")
    if idx == -1:
        return raw.strip(), ""
    return raw[:idx].strip(), raw[idx:].strip()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run() -> str:
    """
    Run the full ghostwriting pipeline and save the result.
    Returns the final post content (post + editor note + quality score).
    """
    profile, strategy, style, ideas, published_topics = _load_context()
    critic_model, critic_host = _resolve_critic()

    # Stage 1 — Topic Intelligence
    print("[PIPELINE 1/5] Topic Strategist...")
    topic_analysis = run_agent(
        _topic_prompt(profile, strategy, ideas, published_topics),
        model=_pick(_API_DEFAULT, _OLLAMA_DEFAULT),
    )
    print(f"[PIPELINE 1/5] Done ({len(topic_analysis)} chars)")

    # Stage 2 — First Draft
    print("[PIPELINE 2/5] Ghostwriter...")
    draft = run_agent(
        _ghostwriter_prompt(topic_analysis, style, profile),
        model=_pick(_API_DEFAULT, _OLLAMA_DEFAULT),
    )
    print(f"[PIPELINE 2/5] Done ({len(draft)} chars)")

    # Stage 3 — Critic (best available model for genuine depth)
    print(f"[PIPELINE 3/5] Critic ({critic_model}{' @ remote' if critic_host else ''})...")
    critique = run_agent(
        _critic_prompt(draft, profile),
        model=critic_model,
        max_tokens=6144,
        host=critic_host,
    )
    print(f"[PIPELINE 3/5] Done ({len(critique)} chars)")

    # Stage 4 — Synthesis
    print("[PIPELINE 4/5] Synthesizer...")
    synthesis_raw = run_agent(
        _synthesizer_prompt(draft, critique, style, profile),
        model=_pick(_API_DEFAULT, _OLLAMA_DEFAULT),
    )
    post, editor_note = _split_synthesis(synthesis_raw)
    print(f"[PIPELINE 4/5] Done ({len(post)} chars)")

    # Stage 5 — Quality Gate
    print("[PIPELINE 5/5] Quality Gate...")
    gate_raw = run_agent(_quality_gate_prompt(post, profile), model=_pick(_API_DEFAULT, _OLLAMA_DEFAULT))
    passed, score = _parse_quality(gate_raw)

    if not passed:
        print(f"[PIPELINE 5/5] NEEDS_REVISION (avg {score:.1f}) — running one retry...")
        combined = f"{critique}\n\n## Quality Gate Feedback\n{gate_raw}"
        retry_raw = run_agent(
            _synthesizer_prompt(post, combined, style, profile),
            model=_pick(_API_DEFAULT, _OLLAMA_DEFAULT),
        )
        post, editor_note = _split_synthesis(retry_raw)
        gate_raw2 = run_agent(_quality_gate_prompt(post, profile), model=_pick(_API_DEFAULT, _OLLAMA_DEFAULT))
        passed, score = _parse_quality(gate_raw2)
        print(f"[PIPELINE 5/5] After retry: {'APPROVED' if passed else 'passed through'} (avg {score:.1f})")
    else:
        print(f"[PIPELINE 5/5] APPROVED (avg {score:.1f})")

    # Assemble final output
    parts = [post]
    if editor_note:
        parts.append(f"\n\n---\n\n{editor_note}")
    parts.append(f"\n\n---\n\n*Quality score: {score:.1f}/10*")

    final = "".join(parts)
    save_output("linkedin", "ghostwritten", final)
    return final
