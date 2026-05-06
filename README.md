# MV BRAIN Hermes Adapter

[한국어 README](README.ko.md)

A small **CLI + Hermes/MCP adapter** for searching MV BRAIN clip metadata and exporting selected moments as downloadable MP4 clips. It is separate from the main [`mv-brain`](https://github.com/hyuk-ju/mv-brain)
repo so it can stay focused on agent integration and MP4 handoff exports.

The adapter lets Hermes or any MCP client ask for useful moments in local video
metadata, export cut lists, and optionally render selected moments into MP4 clips
with `ffmpeg`.

## Why this exists

Hermes is often not running on the same laptop that holds the footage. It may run on a server, remote workstation, or always-on machine near the media.

This version focuses on a simple target: bring footage into the working machine, let MV BRAIN analyze and remember useful moments, then let Hermes export the selected ranges as MP4 clips. Editor-specific project exports are out of scope for this adapter version.

Universal input/output path:

```text
Google Drive / Dropbox / NAS / server folder
  -> rclone or desktop sync
  -> mv-brain ingest
  -> Qdrant clip archive
  -> mv-brain-hermes snapshot-qdrant
  -> Hermes/MCP search
  -> MP4 export with ffmpeg
```

Many editors do not use the same editing tool, and many agent workflows just need the actual MP4 moments. This adapter therefore starts with universal outputs:

- searchable clip metadata
- JSON/CSV cut lists
- individual MP4 clip exports
- rough-cut MP4 preview manifests
- MCP tools for Hermes Agent

## Safe first-run demo

No videos, Qdrant, provider keys, or media processing required:

```bash
python3 -m pip install -e '.[test]'
mv-brain-hermes demo --out data/demo/clips.json
mv-brain-hermes search "neon chorus dance" --clips data/demo/clips.json
mv-brain-hermes export-pack "chorus" --clips data/demo/clips.json --out exports/chorus-pack
```

`export-pack` writes the agent/editor handoff bundle:

```text
cutlist.json          # structured context for agents and scripts
cutlist.csv           # spreadsheet-friendly edit list for editors
preview_manifest.json # rough-cut timeline order before rendering
README.md             # explains the pack and the optional render step
```

The older `export-cutlist` command writes only the metadata cut list under `exports/chorus/`:

```text
cutlist.json
cutlist.csv
README.md
```

## Google Drive / remote footage

If the source footage is in Google Drive, keep Drive as the storage/sync layer and ingest local copies on the machine where MV BRAIN runs.

```bash
rclone config
rclone copy gdrive:mv-footage ./videos

cd ../mv-brain
mv-brain ingest ./videos/*.mp4

cd ../mv-brain-hermes
PYTHONPATH=../mv-brain mv-brain-hermes snapshot-qdrant \
  --out data/mvbrain/clips.json

mv-brain-hermes export-clips "chorus dance" \
  --clips data/mvbrain/clips.json \
  --out exports/chorus-mp4 \
  --limit 3 \
  --render
```

The adapter does not require Google Drive specifically. Any workflow that makes real video files available on the working machine is enough.

## Optional MP4 rendering

When clip metadata points at real local files, add `--render` to cut the selected
moments into MP4 files:

```bash
mv-brain-hermes export-clips "neon dance close-up"   --clips ./my_project/clips.json   --out exports/neon   --limit 5   --render
```

The default render mode re-encodes with H.264/AAC for broad MP4 compatibility.
Without `--render`, it only writes a manifest and never touches media.

## Current stack

This repo is intentionally small. It is a Python adapter, not a full copy of the main MV BRAIN app.

- Python 3.11+
- CLI: `argparse`, `json`, `csv`, `pathlib`, `subprocess`
- Packaging: `setuptools` + `pyproject.toml`
- MCP server: `mcp.server.fastmcp.FastMCP` via the optional `mcp` extra
- Tests: `pytest`
- Optional rendering: `ffmpeg`
- Input: local `clips.json` metadata
- Outputs: `cutlist.json`, `cutlist.csv`, `preview_manifest.json`, `README.md`, optional MP4 clips and `render_manifest.json`

## Difference from the main MV BRAIN repo

The main [`mv-brain`](https://github.com/hyuk-ju/mv-brain) project is the larger app. It includes heavier pieces such as Gemini/Google analysis, embeddings, Qdrant storage, provider key settings, and a web UI.

This adapter does not copy those core systems into a second app. Instead, it can export the main MV BRAIN Qdrant `clip_archive` payloads into a portable `clips.json` snapshot, then let Hermes/MCP search and export that snapshot.

```text
mv-brain ingest/search/embedding/Qdrant
  -> mv-brain-hermes snapshot-qdrant
  -> data/mvbrain/clips.json
  -> Hermes/MCP search/export-pack/export-clips
```

Current status:

- Direct Google/Gemini embedding calls: handled by the main `mv-brain` stack
- Qdrant ingestion/vector creation: handled by the main `mv-brain` stack
- Qdrant clip archive snapshot export: included (`snapshot-qdrant`)
- Provider auth/API-key management: handled by main `mv-brain` or the user's Hermes environment
- Local `clips.json` keyword/label/description search: included
- Hermes/MCP tools: included
- CLI exports: included
- Optional ffmpeg MP4 clip rendering: included

## Metadata format

Input is a JSON file containing either a list of clips or an object with a
`clips` array:

```json
{
  "clips": [
    {
      "id": "clip_001",
      "source": "A001.mp4",
      "source_path": "/absolute/path/to/A001.mp4",
      "start_time": 72.5,
      "end_time": 76.2,
      "labels": ["neon", "dance", "chorus"],
      "description": "High-energy neon close-up for the chorus hook.",
      "score": 0.92
    }
  ]
}
```

## Hermes MCP configuration

Install with the MCP extra, then add this to the Hermes profile config:

```yaml
mcp_servers:
  mvbrain:
    command: "python3"
    args:
      - "-m"
      - "mv_brain_hermes.mcp_server"
    env:
      MV_BRAIN_CLIPS_PATH: "/absolute/path/to/mv-brain-hermes/data/demo/clips.json"
      MV_BRAIN_EXPORT_ROOT: "/absolute/path/to/mv-brain-hermes/exports"
    timeout: 120
    connect_timeout: 30
```

After restarting Hermes, tools are exposed with the `mcp_mvbrain_*` prefix. MCP write tools are constrained to `MV_BRAIN_EXPORT_ROOT`; set it to a dedicated exports folder. MP4 rendering through MCP is disabled unless `MV_BRAIN_ENABLE_RENDER=1` is also set.

Tools:

- `list_clips`
- `search_clips`
- `export_cutlist`
- `export_clip_pack`
- `export_clips`
- `export_preview_manifest`
- `snapshot_qdrant`

## Hermes onboarding files

After cloning the repo, generate a Hermes skill draft, MCP config snippet, and quickstart:

```bash
mv-brain-hermes init-hermes \
  --out hermes_onboarding \
  --repo-path "$(pwd)" \
  --clips "$(pwd)/data/mvbrain/clips.json"
```

This writes:

```text
hermes_onboarding/skill/SKILL.md
hermes_onboarding/mcp_config.yaml
hermes_onboarding/QUICKSTART.md
```

Copy the skill into your Hermes skills folder or use it as an agent-facing runbook.

## Example Hermes prompts

```text
Find 5 high-energy chorus dance clips.
Export those as an agent-readable MP4 handoff pack.
Render the top 3 selected local moments as MP4 clips.
Make a rough-cut preview manifest for neon close-up shots.
```

## Scope

This repo does **not** do heavy video analysis by itself yet. It is an adapter
layer. The main MV BRAIN project can produce richer metadata with scene
analysis, captions, embeddings, and reference matching. This repo focuses on the
agent interface and universal exports.

## Security notes

- No API keys are required for the demo.
- `.env`, generated media, and local data folders are ignored.
- MCP server subprocesses should receive only explicit environment variables.
- Rendering only reads paths present in the supplied local metadata file.
