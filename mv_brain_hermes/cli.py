from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import export_clip_pack, export_clips, export_cutlist, export_preview_manifest, list_clips, search_clips
from .demo import write_demo


def _print(data: object) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mv-brain-hermes")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="write no-media demo clip metadata")
    demo.add_argument("--out", default="data/demo/clips.json")

    listing = sub.add_parser("list", help="list clips from metadata")
    listing.add_argument("--clips", default=None)
    listing.add_argument("--limit", type=int, default=50)
    listing.add_argument("--source-type", default=None)

    search = sub.add_parser("search", help="search clips by natural-language keywords")
    search.add_argument("query")
    search.add_argument("--clips", default=None)
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--source-type", default=None)

    cutlist = sub.add_parser("export-cutlist", help="write JSON/CSV cut list")
    cutlist.add_argument("query")
    cutlist.add_argument("--clips", default=None)
    cutlist.add_argument("--out", required=True)
    cutlist.add_argument("--limit", type=int, default=10)
    cutlist.add_argument("--source-type", default=None)

    pack = sub.add_parser("export-pack", help="write agent/editor handoff pack: cutlist JSON/CSV, preview manifest, README")
    pack.add_argument("query")
    pack.add_argument("--clips", default=None)
    pack.add_argument("--out", required=True)
    pack.add_argument("--limit", type=int, default=8)

    clips = sub.add_parser("export-clips", help="write cut list and optionally render MP4 clips")
    clips.add_argument("query")
    clips.add_argument("--clips", default=None)
    clips.add_argument("--out", required=True)
    clips.add_argument("--limit", type=int, default=5)
    clips.add_argument("--render", action="store_true")
    clips.add_argument("--copy", action="store_true", help="use ffmpeg stream copy instead of H.264/AAC re-encode")

    preview = sub.add_parser("export-preview", help="write a rough-cut preview manifest")
    preview.add_argument("query")
    preview.add_argument("--clips", default=None)
    preview.add_argument("--out", required=True)
    preview.add_argument("--limit", type=int, default=8)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        _print(write_demo(args.out))
    elif args.command == "list":
        _print(list_clips(args.clips, args.limit, args.source_type))
    elif args.command == "search":
        _print(search_clips(args.query, args.clips, args.limit, args.source_type))
    elif args.command == "export-cutlist":
        _print(export_cutlist(args.query, args.clips, args.out, args.limit, args.source_type))
    elif args.command == "export-pack":
        _print(export_clip_pack(args.query, args.clips, args.out, args.limit))
    elif args.command == "export-clips":
        _print(export_clips(args.query, args.clips, args.out, args.limit, args.render, reencode=not args.copy))
    elif args.command == "export-preview":
        _print(export_preview_manifest(args.query, args.clips, args.out, args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
