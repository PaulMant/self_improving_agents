"""
Read-only bridge to Paul's Lab knowledge base.

Configure with PAULS_LAB_PATH in .env.
All public methods return empty values (never raise) so agents degrade
gracefully when the lab is unreachable.

Usage:
    from core import knowledge_client as kb
    style  = kb.get_writing_style()
    drafts = kb.get_pending_drafts("linkedin")
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    Return (meta, body).
    meta values are strings or list[str] (for bracketed YAML lists).
    Quoted string values have their outer quotes stripped.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text

    body = text[m.end():].strip()
    meta: dict = {}

    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, raw = line.partition(":")
        value = raw.strip()

        # Bracketed list: [a, b, c]
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1]
            meta[key.strip()] = [s.strip() for s in inner.split(",") if s.strip()]
            continue

        # Quoted string
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]

        meta[key.strip()] = value

    return meta, body


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def _lab_root() -> Path:
    raw = os.getenv("PAULS_LAB_PATH", "")
    if not raw:
        raise EnvironmentError(
            "PAULS_LAB_PATH is not set. "
            "Add it to .env: PAULS_LAB_PATH=/path/to/Paul's Lab"
        )
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"PAULS_LAB_PATH not found: {path}")
    return path


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_writing_style() -> str:
    """Full content of wiki/synthesis/writing-style.md."""
    return _read(_lab_root() / "wiki" / "synthesis" / "writing-style.md")


def get_pending_drafts(platform: str) -> list[dict]:
    """
    All non-published drafts for a platform ("linkedin" or "blog").

    Each dict has:
        slug            str          — file stem, e.g. draft-linkedin-agent-first
        title           str
        source_concepts list[str]    — wiki concept/entity slugs
        body            str          — markdown body (frontmatter stripped)
        path            str          — absolute path to the draft file
    """
    synthesis_dir = _lab_root() / "wiki" / "synthesis"
    drafts: list[dict] = []

    for p in sorted(synthesis_dir.glob(f"draft-{platform}-*.md")):
        text = _read(p)
        if not text:
            continue
        meta, body = _parse_frontmatter(text)
        if meta.get("status") == "published":
            continue

        concepts = meta.get("source_concepts", [])
        if isinstance(concepts, str):
            concepts = [c.strip() for c in concepts.split(",") if c.strip()]

        drafts.append({
            "slug": p.stem,
            "title": meta.get("title", p.stem),
            "source_concepts": concepts,
            "body": body,
            "path": str(p),
        })

    return drafts


def get_wiki_context(slugs: list[str]) -> str:
    """
    Return concatenated content for specific concept/entity slugs.
    Searches wiki/concepts/ first, then wiki/entities/ for each slug.
    Returns empty string if none found.
    """
    root = _lab_root()
    search_dirs = [root / "wiki" / "concepts", root / "wiki" / "entities"]
    parts: list[str] = []

    for slug in slugs:
        for d in search_dirs:
            p = d / f"{slug}.md"
            if p.exists():
                content = _read(p)
                if content:
                    _, body = _parse_frontmatter(content)
                    parts.append(f"### [{slug}]\n{body}")
                break

    return "\n\n".join(parts)


def get_ideas() -> str:
    """
    Ideas from 'Linkedin Post Ideas.md' and raw/ideas/*.md.
    Returns empty string if neither source exists.
    """
    root = _lab_root()
    parts: list[str] = []

    ideas_file = root / "Linkedin Post Ideas.md"
    if ideas_file.exists():
        content = _read(ideas_file)
        if content:
            parts.append(f"## Curated LinkedIn Ideas\n{content}")

    ideas_dir = root / "raw" / "ideas"
    if ideas_dir.is_dir():
        for p in sorted(ideas_dir.glob("*.md")):
            content = _read(p)
            if content:
                parts.append(f"## {p.stem}\n{content}")

    return "\n\n".join(parts)


def get_published_slugs(platform: str) -> list[str]:
    """
    Slugs of already-published content for a platform.
    Useful to avoid generating duplicate topics.
    """
    published_dir = _lab_root() / "published" / platform
    if not published_dir.is_dir():
        return []
    return [p.stem for p in sorted(published_dir.glob("*.md"))]


def get_published_topics(platform: str) -> list[str]:
    """
    Human-readable topic descriptions for already-published posts.
    Returns the post title (from frontmatter) when available, falls back to
    the first non-empty body line, then to the file stem.
    """
    published_dir = _lab_root() / "published" / platform
    if not published_dir.is_dir():
        return []

    topics: list[str] = []
    for p in sorted(published_dir.glob("*.md")):
        text = _read(p)
        if not text:
            topics.append(p.stem)
            continue
        meta, body = _parse_frontmatter(text)
        title = meta.get("title") or meta.get("Title")
        if not title:
            first_line = next((l.strip() for l in body.splitlines() if l.strip()), "")
            title = first_line[:120] if first_line else p.stem
        topics.append(title)

    return topics


def mark_draft_published(draft_path: str) -> None:
    """
    Set status: published in a draft file's frontmatter.
    Call this after Paul confirms a post went live.
    Does nothing if the file doesn't exist or has no status field.
    """
    p = Path(draft_path).resolve()
    if not p.exists():
        return
    text = _read(p)
    updated = text.replace("status: draft", "status: published", 1)
    if updated != text:
        p.write_text(updated, encoding="utf-8")
        print(f"[KNOWLEDGE] Marked as published: {p.name}")
