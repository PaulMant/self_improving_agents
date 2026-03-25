import os
from datetime import datetime, timedelta

OUTPUT_DIR = "output"


def save_output(category: str, filename: str, content: str) -> str:
    """Save content to output/{category}/YYYY-MM-DD_{filename}.md"""
    folder = os.path.join(OUTPUT_DIR, category)
    os.makedirs(folder, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(folder, f"{date_str}_{filename}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {filename.replace('_', ' ').title()} — {date_str}\n\n")
        f.write(content)
    print(f"[OUTPUT] Saved: {path}")
    return path


def get_recent_outputs(days: int = 7) -> str:
    """Return a text summary of output files from the last N days."""
    cutoff = datetime.now() - timedelta(days=days)
    lines = []
    if not os.path.exists(OUTPUT_DIR):
        return "No outputs yet."
    for category in os.listdir(OUTPUT_DIR):
        cat_path = os.path.join(OUTPUT_DIR, category)
        if not os.path.isdir(cat_path):
            continue
        for fname in sorted(os.listdir(cat_path)):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(cat_path, fname)
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
            if mtime >= cutoff:
                lines.append(f"- [{category}] {fname}")
    return "\n".join(lines) if lines else "No recent outputs."


def get_today_outputs() -> list[str]:
    """Return paths of all output files created today."""
    today = datetime.now().strftime("%Y-%m-%d")
    result = []
    if not os.path.exists(OUTPUT_DIR):
        return result
    for category in os.listdir(OUTPUT_DIR):
        cat_path = os.path.join(OUTPUT_DIR, category)
        if not os.path.isdir(cat_path):
            continue
        for fname in os.listdir(cat_path):
            if fname.startswith(today):
                result.append(os.path.join(cat_path, fname))
    return result
