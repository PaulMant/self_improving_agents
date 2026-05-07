import ollama
import time

MAX_RETRIES = 3
MAX_PROMPT = 8000

def run_agent(prompt, model=None):

    from core.config import OLLAMA_MODEL
    _model = model or OLLAMA_MODEL

    for attempt in range(MAX_RETRIES):
        try:
            prompt = prompt[:MAX_PROMPT]
            response = ollama.chat(
                model=_model,
                messages=[{"role": "user", "content": prompt}],
                options={"num_predict": 500}
            )

            result = response["message"]["content"]

            with open("memory/growth_log.md", "a") as f:
                f.write("\n\n" + result)

            return result

        except Exception as e:
            print(f"Agent failed (attempt {attempt+1}): {e}")
            time.sleep(5)

    return "Agent failed after retries."