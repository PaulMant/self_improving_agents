#!/usr/bin/env python3
"""Dashboard server for the autonomous growth agents.

Usage:
    pip install fastapi uvicorn
    uvicorn server:app --reload --port 8000
    # then open http://localhost:8000
"""

import asyncio
import json
import re
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"
DATA_DIR = ROOT / "data"
FRONTEND_DIR = ROOT / "frontend"

app = FastAPI(title="Growth Engine")

AGENTS: dict[str, dict] = {
    "linkedin": {
        "label": "LinkedIn Posts",
        "desc": "3 post drafts generated from your knowledge base",
        "icon": "💼",
        "category": "linkedin",
    },
    "linkedin_pipeline": {
        "label": "LinkedIn Pipeline",
        "desc": "5-stage pipeline: strategy → ghostwrite → critique → synthesize → quality gate",
        "icon": "⚡",
        "category": "linkedin",
    },
    "article": {
        "label": "Article",
        "desc": "Long-form technical piece for Dev.to or your blog",
        "icon": "✍️",
        "category": "articles",
    },
    "hn": {
        "label": "Hacker News",
        "desc": "Show HN or Ask HN post",
        "icon": "🟠",
        "category": "hn",
    },
    "reddit": {
        "label": "Reddit",
        "desc": "r/forhire post to attract inbound leads",
        "icon": "🔴",
        "category": "reddit",
    },
    "outreach": {
        "label": "Outreach",
        "desc": "Personalized email templates for cold outreach",
        "icon": "📧",
        "category": "outreach",
    },
    "opportunity": {
        "label": "Opportunity Research",
        "desc": "Market opportunity analysis and lead research",
        "icon": "🔍",
        "category": "opportunities",
    },
    "optimizer": {
        "label": "Strategy Optimizer",
        "desc": "Self-improve the strategy based on performance data",
        "icon": "📈",
        "category": "optimizer",
    },
}


def _read_json(name: str) -> dict:
    for suffix in (f"{name}.json", f"{name}.example.json"):
        p = DATA_DIR / suffix
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _extract_score(content: str) -> float | None:
    m = re.search(r"\*Quality score:\s*([\d.]+)/10\*", content)
    return float(m.group(1)) if m else None


@app.get("/api/profile")
def get_profile() -> dict:
    return _read_json("profile")


@app.get("/api/strategy")
def get_strategy() -> dict:
    return _read_json("strategy")


@app.get("/api/agents")
def get_agents() -> dict:
    return AGENTS


@app.get("/api/outputs")
def list_outputs() -> dict:
    if not OUTPUT_DIR.exists():
        return {}
    result: dict[str, list] = {}
    for cat in sorted(OUTPUT_DIR.iterdir()):
        if not cat.is_dir():
            continue
        files = []
        for f in sorted(cat.glob("*.md"), reverse=True):
            text = f.read_text(encoding="utf-8")
            stat = f.stat()
            preview = " ".join(text[:400].split())[:220]
            files.append(
                {
                    "name": f.name,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "score": _extract_score(text),
                    "preview": preview,
                }
            )
        if files:
            result[cat.name] = files
    return result


@app.get("/api/outputs/{category}/{filename}")
def get_output(category: str, filename: str) -> dict:
    if ".." in category or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid path")
    p = OUTPUT_DIR / category / filename
    if not p.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    text = p.read_text(encoding="utf-8")
    return {"content": text, "score": _extract_score(text)}


@app.get("/api/run/{agent}")
async def run_agent(agent: str) -> StreamingResponse:
    if agent not in AGENTS:
        raise HTTPException(status_code=400, detail="Unknown agent")

    async def _stream():
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(ROOT / "run_agents.py"),
            "--agent",
            agent,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(ROOT),
        )
        async for raw in proc.stdout:  # type: ignore[union-attr]
            line = raw.decode(errors="replace").rstrip()
            yield f"data: {json.dumps({'line': line})}\n\n"
        await proc.wait()
        payload = json.dumps(
            {"done": True, "code": proc.returncode, "category": AGENTS[agent]["category"]}
        )
        yield f"data: {payload}\n\n"

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/{path:path}")
def spa_fallback(path: str) -> FileResponse:
    static = FRONTEND_DIR / path
    if static.is_file():
        return FileResponse(static)
    return FileResponse(FRONTEND_DIR / "index.html")
