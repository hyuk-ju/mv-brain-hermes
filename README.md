# MV BRAIN Hermes Adapter

A small **Hermes/MCP adapter** for local-first music-video clip retrieval and
cut exports. It is separate from the main [`mv-brain`](https://github.com/hyuk-ju/mv-brain)
repo so it can stay focused on agent integration.

The adapter lets Hermes or any MCP client ask for useful moments in local video
metadata, export cut lists, and optionally render selected moments into MP4 clips
with `ffmpeg`.

## Why this exists

Many editors do not use Final Cut Pro. Some use Premiere, DaVinci Resolve,
CapCut, mobile editors, or just want a quick preview. Instead of only exporting
FCPXML, this adapter starts with universal outputs:

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
mv-brain-hermes export-cutlist "chorus" --clips data/demo/clips.json --out exports/chorus
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

## Optional MP4 rendering

When clip metadata points at real local files, add `--render` to cut the selected
moments into MP4 files:

```bash
mv-brain-hermes export-clips "neon dance close-up"   --clips ./my_project/clips.json   --out exports/neon   --limit 5   --render
```

The default render mode re-encodes with H.264/AAC for compatibility with
Premiere, DaVinci, CapCut, and mobile tools. Without `--render`, it only writes a
manifest and never touches media.

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
      MV_BRAIN_CLIPS_PATH: "/home/dev/mv-brain-hermes/data/demo/clips.json"
    timeout: 120
    connect_timeout: 30
```

After restarting Hermes, tools are exposed with the `mcp_mvbrain_*` prefix:

- `list_clips`
- `search_clips`
- `export_cutlist`
- `export_clip_pack`
- `export_clips`
- `export_preview_manifest`

## Example Hermes prompts

```text
Find 5 high-energy chorus dance clips.
Export those as an agent-readable clip pack for CapCut and future agents.
Export those as a cut list for CapCut.
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
