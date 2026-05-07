import json

from core.runner import run_agent
from core.output_manager import save_output
from prompts.loader import load_prompt


def _load_knowledge() -> tuple[str, list]:
    """
    Try to load writing style and pending blog drafts from Paul's Lab.
    Returns ("", []) silently if PAULS_LAB_PATH is not set or unreachable.
    """
    try:
        from core import knowledge_client as kb
        style = kb.get_writing_style()
        drafts = kb.get_pending_drafts("blog")
        return style, drafts
    except EnvironmentError:
        return "", []
    except Exception as e:
        print(f"[KNOWLEDGE] Load failed, using fallback prompts: {e}")
        return "", []


def _draft_prompt(draft: dict, style: str, wiki_ctx: str, profile: dict) -> str:
    sections = [
        "You are finalizing a blog article draft for Paul Mantello.",
        "## Writing Style Profile — adapt to long-form\n" + style,
        "## Draft to Finalize\n" + draft["body"],
    ]
    if wiki_ctx:
        sections.append("## Relevant Context (from Paul's knowledge base)\n" + wiki_ctx)
    sections += [
        f"## Author Profile\n{json.dumps(profile, indent=2)}",
        (
            "Expand and polish this draft into a complete blog article (~900 words).\n"
            "Maintain Paul's voice: direct, evidence-based, no hype, no hedging.\n"
            "Return ONLY the article — no meta-commentary, no preamble."
        ),
    ]
    return "\n\n".join(sections)


def run():
    profile = json.load(open("data/profile.json"))
    strategy = json.load(open("data/strategy.json"))

    style, drafts = _load_knowledge()

    if style:
        print(f"[KNOWLEDGE] Style loaded ({len(style)} chars) | Blog drafts: {len(drafts)}")

    if drafts:
        draft = drafts[0]
        print(f"[ARTICLE] Mode: finalize draft '{draft['slug']}'")

        wiki_ctx = ""
        if draft["source_concepts"]:
            try:
                from core import knowledge_client as kb
                wiki_ctx = kb.get_wiki_context(draft["source_concepts"])
            except Exception:
                pass

        effective_style = style or ""
        prompt = _draft_prompt(draft, effective_style, wiki_ctx, profile)
        result = run_agent(prompt, max_tokens=6000)
        output = f"<!-- source: {draft['path']} -->\n\n{result}"

    else:
        print("[ARTICLE] Mode: generate from theme")
        # Rotate themes offset by 2 from linkedin so content doesn't repeat
        themes = strategy["content_themes"]
        theme = themes[(strategy["cycle_count"] + 2) % len(themes)]

        prompt = (
            load_prompt("article")
            + f"\n\nProfile:\n{json.dumps(profile, indent=2)}"
            + f"\n\nArticle theme: {theme}"
        )
        result = run_agent(prompt, max_tokens=6000)
        output = result

    save_output("articles", "article", output)
    print("[ARTICLE] Article saved.")
    return output
