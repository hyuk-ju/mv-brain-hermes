# Security Policy

## Supported versions

This project is pre-1.0. Security fixes are made on the default branch.

## Reporting a vulnerability

Please open a private GitHub security advisory or contact the maintainer before publishing exploit details.

Do not include API keys, private media paths, or private footage in reports. Redact secrets and share only the minimum reproduction needed.

## Local security model

`mv-brain-hermes` is a local CLI/MCP adapter. It is designed to read explicit `clips.json` metadata and write export files under an allowed export folder.

Important boundaries:

- The no-media demo does not require API keys, Qdrant, provider calls, or real footage.
- MP4 rendering is opt-in with `--render` in CLI mode.
- MCP rendering requires `MV_BRAIN_ENABLE_RENDER=1`.
- MCP write tools should use a dedicated `MV_BRAIN_EXPORT_ROOT`.
- Provider keys, visual analysis, embeddings, and Qdrant ingestion belong to the main `mv-brain` stack, not this adapter.

Never commit `.env`, API keys, private footage, generated media, Qdrant data, or local export folders.
