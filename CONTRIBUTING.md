# Contributing

Thanks for checking out MV BRAIN Hermes Adapter.

## Development setup

```bash
python3 -m pip install -e '.[test]'
python3 -m compileall -q mv_brain_hermes
python3 -m pytest -q
```

Optional MCP support:

```bash
python3 -m pip install -e '.[mcp,test]'
```

## Safe contribution rules

- Do not commit `.env`, API keys, private footage, generated media, local Qdrant data, or export folders.
- Tests must not require real media, cloud providers, Qdrant, or paid API calls.
- Keep rendering opt-in. CLI rendering uses `--render`; MCP rendering requires `MV_BRAIN_ENABLE_RENDER=1`.
- Keep MCP writes constrained to `MV_BRAIN_EXPORT_ROOT`.
- Document whether a feature belongs to this adapter or the main `mv-brain` project.

## Pull request checklist

- [ ] `python3 -m compileall -q mv_brain_hermes`
- [ ] `python3 -m pytest -q`
- [ ] README commands match implemented CLI/MCP tools
- [ ] No secrets, private paths, media files, generated data, or local exports are tracked
