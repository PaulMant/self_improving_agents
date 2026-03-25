import json
from core.runner import run_agent
from core.output_manager import save_output
from prompts.loader import load_prompt
from core.config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD


def run():
    profile = json.load(open("data/profile.json"))

    prompt = (
        load_prompt("reddit")
        + f"\n\nProfile:\n{json.dumps(profile, indent=2)}"
    )

    result = run_agent(prompt)
    save_output("reddit", "post", result)

    if all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD]):
        _post_to_reddit(result)
    else:
        print("[REDDIT] No credentials set — post saved locally only.")

    return result


def _post_to_reddit(content: str):
    try:
        import praw

        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD,
            user_agent="growth-agent/1.0 by u/" + REDDIT_USERNAME,
        )

        lines = content.strip().split("\n")
        # First line should be the title (without [FOR HIRE] prefix since we add it)
        raw_title = lines[0].replace("[FOR HIRE]", "").strip()
        title = f"[FOR HIRE] {raw_title}"
        body = "\n".join(lines[1:]).strip()

        subreddit = reddit.subreddit("forhire")
        post = subreddit.submit(title, selftext=body)
        print(f"[REDDIT] Posted: https://reddit.com{post.permalink}")
    except ImportError:
        print("[REDDIT] praw not installed. Run: pip install praw")
    except Exception as e:
        print(f"[REDDIT] Error posting: {e}")
