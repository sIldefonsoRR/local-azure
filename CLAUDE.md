# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Local stand-in for Azure OpenAI. Apps written against the Azure OpenAI SDK point at `http://localhost:4000` and get responses from local Ollama models instead of real Azure. No tests, lint, or build step exist.

## Commands

```bash
# Start stack (Ollama + model pull + LiteLLM proxy on :4000)
docker compose up -d

# Watch first-run model download / proxy startup
docker compose logs -f ollama fake-azure

# Smoke test via Azure SDK (uses local venv, Python 3.15; .venv is gitignored)
python3 -m venv .venv             # only if .venv doesn't exist
source .venv/bin/activate
pip install -r requirements.txt   # only if venv is missing deps
python call-azure.py              # prompts for a question; streams reply, then embeds it

# Both scripts read stdin via input(); pipe input for non-interactive runs
echo "What is the capital of Italy?" | python call-azure.py

# Interactive chat that remembers the last 5 turns (type exit/quit to stop)
python call-azure-with-memory.py
printf 'What is the capital of Italy?\nWhat cities are around it?\nquit\n' | python call-azure-with-memory.py

# Reload after editing litellm_config.yaml
docker compose restart fake-azure
```

## Architecture

Two compose services:

1. `ollama` — serves models on container port `11434`, published on the host as `127.0.0.1:11435` (not 11434: a native Ollama app on the host may already hold `127.0.0.1:11434`, and host `localhost:11434` would reach that one, not the container). `fake-azure` reaches it over the compose network at `ollama:11434`, so the host port is only for debugging, e.g. `curl localhost:11435/api/tags`. Data persisted in `ollama_data` volume. data persisted in `ollama_data` volume. Its overridden `command` starts `ollama serve` in the background, pulls `llama3.2` and `nomic-embed-text`, then `wait`s on the server. A `trap` forwards SIGTERM so `docker compose stop` is clean. Pull failures only log `WARN:` (so offline restarts with cached models still work). Healthcheck runs `ollama show` on both models, so it turns healthy only after the pull; `start_period: 15m` covers first-run download time.
2. `fake-azure` — LiteLLM proxy (`ghcr.io/berriai/litellm:main-latest`) on `:4000`, configured by `litellm_config.yaml` mounted at `/app/config.yaml`. `depends_on` `ollama: service_healthy`, so first startup is slow.

Shell variables in the `ollama` command use `$$` to escape Compose interpolation.

**Deployment mapping** lives in `litellm_config.yaml`: each `model_name` is the fake Azure *deployment name* clients send as `model=`, mapped to an Ollama model:
- `gpt-4o` → `ollama/llama3.2`
- `text-embedding-3-small` → `ollama/nomic-embed-text`

To expose a new deployment: add a `model_list` entry (with `api_base: http://ollama:11434` — container hostname, not localhost) and, if it's a new Ollama model, add an `ollama pull` line to the `ollama` service's `command` **and** an `ollama show` check to its healthcheck in `docker-compose.yml` (otherwise `fake-azure` may start before the model is downloaded).

`litellm_settings.drop_params: true` is required: the OpenAI SDK sends `encoding_format=base64` on embeddings calls, which Ollama rejects with `UnsupportedParamsError`.

**Auth**: no master key is set (`LITELLM_DANGEROUSLY_PERMIT_WEAK_OR_UNSET_MASTER_KEY=true`), so any `api_key` works. Clients use `AzureOpenAI(azure_endpoint="http://localhost:4000", api_key=<anything>, api_version=...)` — see `call-azure.py`. Local-dev only: port 4000 is published on `127.0.0.1` only (`host.docker.internal:4000` still works from other containers); keep it that way.
