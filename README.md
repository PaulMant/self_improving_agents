# Autonomous Growth Agents

Personal growth engine for Paul Mantello. Generates LinkedIn posts, technical articles, community content, and outreach — grounded in a curated knowledge base when available.

Runs against the Claude API (default) or a local Ollama model.

---

## Agents

| Agent | Output |
|-------|--------|
| `linkedin_agent` | 1 finalized LinkedIn post (from draft queue) or 3 generated posts |
| `article_agent` | 1 finalized blog article (from draft queue) or 1 generated article |
| `hn_agent` | Hacker News post draft |
| `reddit_agent` | Reddit r/forhire post |
| `outreach_agent` | Outreach email templates |
| `opportunity_agent` | Market/opportunity research |
| `optimizer_agent` | Strategy optimization notes |
| `seo_agent` | SEO keywords and landing page ideas |
| `community_agent` | Reddit and HN discussion starters |
| `design_agent` | Landing page improvement suggestions |
| `partnerships_agent` | Integration and partnership opportunities |
| `analytics_agent` | Growth strategy review |
| `prompt_optimizer` | Self-improves agent prompts based on output quality |

---

## Setup

**Requirements:** Python 3.10+

```bash
pip install -r requirements.txt
```

**Configuration:**

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required for Claude API backend
ANTHROPIC_API_KEY=sk-ant-...

# Backend: "api" (Claude, default) or "ollama" (local)
LLM_BACKEND=api

# Optional: connect to Paul's Lab knowledge base (see below)
PAULS_LAB_PATH=/absolute/path/to/Paul's Lab
```

**Profile and strategy:**

```bash
cp data/profile.example.json data/profile.json
cp data/strategy.example.json data/strategy.json
```

Fill in `profile.json` (your bio, skills, services) and `strategy.json` (positioning, themes, cycle count).

---

## Usage

```bash
# Run all agents
python run_agents.py

# Run a single agent
python run_agents.py --agent linkedin
python run_agents.py --agent article
python run_agents.py --agent hn

# Use local Ollama instead of Claude API
python run_agents.py --backend ollama

# Available agents: linkedin, article, hn, reddit, outreach, opportunity, optimizer
```

Outputs are saved to `output/<category>/YYYY-MM-DD_<name>.md`.

---

## Knowledge Base Integration

When `PAULS_LAB_PATH` is set, the `linkedin_agent` and `article_agent` connect to Paul's Lab (second brain) and operate in **draft-first mode**:

1. **Check for pending drafts** in `wiki/synthesis/draft-{platform}-*.md`
2. **Load wiki context** — fetches the concept and entity pages that grounded each draft
3. **Finalize** the draft using the living `wiki/synthesis/writing-style.md` as the style guide (updated after every published post)
4. Once all drafts are consumed, switch to **generation mode** — still using `writing-style.md` and curated ideas from `raw/ideas/`

**Without `PAULS_LAB_PATH`:** agents fall back to static prompts, no behavioral change.

### Marking a draft as published

After Paul confirms a post went live on LinkedIn:

```python
from core import knowledge_client as kb
kb.mark_draft_published("/path/to/wiki/synthesis/draft-linkedin-agent-first.md")
```

This sets `status: published` in the frontmatter so the agent won't pick it up again. Then run the PUBLISH workflow in Paul's Lab to update `writing-style.md`.

---

## Local Ollama backend

```bash
ollama pull qwen3:8b
python run_agents.py --backend ollama
```

Any model available in Ollama works. `qwen3:8b` is the default; override with `OLLAMA_MODEL` in `.env`.
