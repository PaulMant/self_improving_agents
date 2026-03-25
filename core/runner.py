"""
Unified LLM runner — dispatches to Claude API or local Ollama.

Backend is selected by core.config.LLM_BACKEND ("api" or "ollama").
Set at startup via --backend CLI flag or LLM_BACKEND env var.
"""
import os


def run_agent(prompt: str, model: str = None, max_tokens: int = 4096, thinking: bool = False) -> str:
    """
    Run a prompt through the configured LLM backend.

    Args:
        prompt:     The full prompt string.
        model:      Override the default model for this call.
        max_tokens: Maximum tokens to generate (Claude only; Ollama uses OLLAMA_MODEL default).
        thinking:   Enable adaptive thinking (Claude Opus only).

    Returns:
        The model's text response.
    """
    # Import here so the backend can be overridden via os.environ before any agent runs
    from core.config import LLM_BACKEND

    if LLM_BACKEND == "ollama":
        return _run_ollama(prompt, model)
    else:
        return _run_claude(prompt, model, max_tokens, thinking)


# --- Claude API backend ---

def _run_claude(prompt: str, model: str, max_tokens: int, thinking: bool) -> str:
    import time
    import anthropic
    from core.config import ANTHROPIC_API_KEY

    _model = model or "claude-sonnet-4-6"
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    kwargs = dict(
        model=_model,
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
            print(f"[CLAUDE] Rate limited. Waiting {wait}s (attempt {attempt+1}/3)")
            time.sleep(wait)
        except anthropic.APIStatusError as e:
            if e.status_code >= 500:
                print(f"[CLAUDE] Server error ({e.status_code}), retry in {5*(attempt+1)}s")
                time.sleep(5 * (attempt + 1))
            else:
                raise
        except anthropic.APIConnectionError:
            print(f"[CLAUDE] Network error, retry in {5*(attempt+1)}s")
            time.sleep(5 * (attempt + 1))

    raise RuntimeError("Claude API failed after 3 attempts")


# --- Ollama backend ---

def _run_ollama(prompt: str, model: str) -> str:
    import time
    import ollama as _ollama
    from core.config import OLLAMA_MODEL

    _model = model or OLLAMA_MODEL
    MAX_PROMPT = 12000  # local models can handle more context than the old 8K limit

    for attempt in range(3):
        try:
            response = _ollama.chat(
                model=_model,
                messages=[{"role": "user", "content": prompt[:MAX_PROMPT]}],
                options={"num_predict": 2048},
            )
            return response["message"]["content"]
        except Exception as e:
            print(f"[OLLAMA] Failed (attempt {attempt+1}/3): {e}")
            time.sleep(5)

    raise RuntimeError(f"Ollama ({_model}) failed after 3 attempts")
