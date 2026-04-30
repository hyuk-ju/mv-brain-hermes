# MV BRAIN Hermes Adapter — Contributor Guide

This repo is a small Hermes/MCP-facing adapter inspired by `hyuk-ju/mv-brain`.
It focuses on safe local metadata search, cut-list exports, and optional MP4
clip rendering via ffmpeg.

## Safe Defaults

- Do not commit `.env`, API keys, private footage, generated media, or local DB data.
- Tests must not require real media, cloud providers, Qdrant, or paid API calls.
- MP4 rendering is opt-in (`render=true` / `--render`) and should only read local paths
  explicitly present in the input metadata.

## Local Checks

```bash
python3 -m compileall -q mv_brain_hermes
python3 -m pytest -q
```

Optional MCP dependency:

```bash
python3 -m pip install -e '.[mcp]'
```
