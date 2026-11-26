# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Local stand-in for Azure OpenAI. Apps written against the Azure OpenAI SDK point at `http://localhost:4000` and get responses from local Ollama models instead of real Azure. No tests, lint, or build step exist.

## Commands

```bash
# Start stack (Ollama + model pull + LiteLLM proxy on :4000)
docker compose up -d

# Watch first-run model download / proxy startup
docker compose logs -f ollama-pull fake-azure

# Smoke test via Azure SDK (uses local venv, Python 3.15)
source .venv/bin/activate
pip install -r requirements.txt   # only if venv is missing deps
python call_azure.py

# Reload after editing litellm_config.yaml
docker compose restart fake-azure
```

## Architecture

Three compose services, started in order via `depends_on` conditions:

1. `ollama` — serves models on `:11434`, data persisted in `ollama_data` volume.
2. `ollama-pull` — one-shot job; pulls `llama3.2` and `nomic-embed-text` into the shared volume, then exits. `fake-azure` waits for it to complete successfully, so first startup is slow.
3. `fake-azure` — LiteLLM proxy (`ghcr.io/berriai/litellm:main-latest`) on `:4000`, configured by `litellm_config.yaml` mounted at `/app/config.yaml`.

**Deployment mapping** lives in `litellm_config.yaml`: each `model_name` is the fake Azure *deployment name* clients send as `model=`, mapped to an Ollama model:
- `gpt-4o` → `ollama/llama3.2`
- `text-embedding-3-small` → `ollama/nomic-embed-text`

To expose a new deployment: add a `model_list` entry (with `api_base: http://ollama:11434` — container hostname, not localhost) and, if it's a new Ollama model, add an `ollama pull` line to the `ollama-pull` command in `docker-compose.yml`.

`litellm_settings.drop_params: true` is required: the OpenAI SDK sends `encoding_format=base64` on embeddings calls, which Ollama rejects with `UnsupportedParamsError`.

**Auth**: no master key is set (`LITELLM_DANGEROUSLY_PERMIT_WEAK_OR_UNSET_MASTER_KEY=true`), so any `api_key` works. Clients use `AzureOpenAI(azure_endpoint="http://localhost:4000", api_key=<anything>, api_version=...)` — see `call_azure.py`. Local-dev only; do not expose port 4000.
