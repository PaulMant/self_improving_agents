import json

from core.runner import run_agent
from core.output_manager import save_output
from prompts.loader import load_prompt


def _load_knowledge() -> tuple[str, list, str]:
    """
    Try to load writing style, pending drafts, and ideas from Paul's Lab.
    Returns ("", [], "") silently if PAULS_LAB_PATH is not set or unreachable.
    """
    try:
        from core import knowledge_client as kb
        style = kb.get_writing_style()
        drafts = kb.get_pending_drafts("linkedin")
        ideas = kb.get_ideas()
        return style, drafts, ideas
    except EnvironmentError:
        return "", [], ""
    except Exception as e:
        print(f"[KNOWLEDGE] Load failed, using fallback prompts: {e}")
        return "", [], ""


def _draft_prompt(draft: dict, style: str, wiki_ctx: str, profile: dict) -> str:
    sections = [
        "You are finalizing a LinkedIn draft for Paul Mantello.",
        "## Writing Style Profile — follow this exactly\n" + style,
        "## Draft to Finalize\n" + draft["body"],
    ]
    if wiki_ctx:
        sections.append("## Relevant Context (from Paul's knowledge base)\n" + wiki_ctx)
    sections += [
        f"## Author Profile\n{json.dumps(profile, indent=2)}",
        (
            "Polish this draft into a publish-ready LinkedIn post.\n"
            "Return ONLY the post text — no preamble, no explanation.\n"
            "Target: 200–280 words, French, zero hashtags."
        ),
    ]
    return "\n\n".join(sections)


def _generation_prompt(style: str, ideas: str, profile: dict, strategy: dict) -> str:
    themes = strategy["content_themes"]
    theme = themes[strategy["cycle_count"] % len(themes)]

    sections = [
        "You are writing LinkedIn posts for Paul Mantello.",
        "## Writing Style Profile — follow this exactly\n" + style,
    ]
    if ideas:
        sections.append("## Curated Ideas — use as inspiration if relevant\n" + ideas)
    sections += [
        f"## Focus Theme\n{theme}",
        f"## Current Positioning\n{strategy['current_positioning']}",
        f"## Author Profile\n{json.dumps(profile, indent=2)}",
        (
            "Generate exactly 3 LinkedIn posts separated by the delimiter '---POST---'.\n"
            "Each post MUST follow the style profile above precisely.\n"
            "Vary the formats: Insight post, Story post, Opinion post."
        ),
    ]
    return "\n\n".join(sections)


def run():
    profile = json.load(open("data/profile.json"))
    strategy = json.load(open("data/strategy.json"))

    style, drafts, ideas = _load_knowledge()

    if style:
        print(f"[KNOWLEDGE] Style loaded ({len(style)} chars) | Drafts: {len(drafts)}")

    if drafts:
        draft = drafts[0]
        print(f"[LINKEDIN] Mode: finalize draft '{draft['slug']}'")

        wiki_ctx = ""
        if draft["source_concepts"]:
            try:
                from core import knowledge_client as kb
                wiki_ctx = kb.get_wiki_context(draft["source_concepts"])
            except Exception:
                pass

        effective_style = style or load_prompt("linkedin")
        prompt = _draft_prompt(draft, effective_style, wiki_ctx, profile)
        result = run_agent(prompt)
        output = f"<!-- source: {draft['path']} -->\n\n{result}"

    else:
        print("[LINKEDIN] Mode: generate new posts")
        effective_style = style or load_prompt("linkedin")
        prompt = _generation_prompt(effective_style, ideas, profile, strategy)
        result = run_agent(prompt)
        output = result

    save_output("linkedin", "posts", output)
    return output
