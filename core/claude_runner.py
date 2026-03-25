import time
import anthropic
from core.config import ANTHROPIC_API_KEY

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def run_agent(prompt: str, model: str = "claude-sonnet-4-6", max_tokens: int = 4096, thinking: bool = False) -> str:
    """
    Run a Claude agent with retry logic and streaming.
    Returns the text response as a string.
    """
    client = _get_client()
    kwargs = dict(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    if thinking:
        kwargs["thinking"] = {"type": "adaptive"}

    for attempt in range(3):
        try:
            with client.messages.stream(**kwargs) as stream:
                return stream.get_final_message().content[0].text
        except anthropic.RateLimitError as e:
            wait = int(e.response.headers.get("retry-after", 30))
            print(f"[RUNNER] Rate limited. Waiting {wait}s (attempt {attempt+1}/3)")
            time.sleep(wait)
        except anthropic.APIStatusError as e:
            if e.status_code >= 500:
                print(f"[RUNNER] Server error ({e.status_code}), retry in {5 * (attempt+1)}s")
                time.sleep(5 * (attempt + 1))
            else:
                raise
        except anthropic.APIConnectionError:
            print(f"[RUNNER] Network error, retry in {5 * (attempt+1)}s")
            time.sleep(5 * (attempt + 1))

    raise RuntimeError("Claude API failed after 3 attempts")
