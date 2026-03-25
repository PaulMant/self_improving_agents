
# Autonomous Growth Agents (Local & Free)

Runs a small autonomous SaaS growth team locally using Ollama.

Agents:
- orchestrator
- seo_agent
- community_agent
- design_agent
- partnerships_agent
- analytics_agent
- prompt_optimizer (self‑improving system)

Requirements:

Python 3.10+
Ollama installed

Recommended models:

ollama pull qwen2.5:14b
ollama pull mistral:7b
ollama pull llama3:8b
ollama pull phi3:mini
ollama pull qwen2.5:7b

Install python deps:

pip install schedule

Run:

python run_agents.py

The system will execute a weekly autonomous growth loop.
