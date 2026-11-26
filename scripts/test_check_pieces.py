#!/usr/bin/env python3
"""Run test_check_text.py and test_check_structure.py on every piece the content log marks review, final or posted.

Usage:
  python3 scripts/test_check_pieces.py [--all]

Reads workspace/content-log.md. For each row whose status starts with review, final or posted
(all rows with --all), checks the piece's final copy (article.md, post.md or page.md) or else its
draft.md, with its visuals.md when there is one, the 200-word cap for LinkedIn posts, and the 880-word cap (a 4-minute read) for blog posts dated from 2026-11-25.
Then test_check_structure.py confirms the piece went through the loop: a brief with a reader, a takeaway and a
terms table; numbers and links traced to the evidence ledger, links with a check date; a limits section in
articles and portfolio pages; the same status in the brief and the log; no open marker once final.
Parked, idea and drafting pieces are skipped, but a piece folder the log does not list at all is an error: it
would dodge every check. Exit 1 when any checked piece has errors.
The voice library, workspace/tone-of-voice/, is never checked, even when a log row points into it: it keeps the
user's published posts, letters and bios exactly as they wrote them.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_check_structure  # noqa: E402
import test_check_text  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "workspace" / "content-log.md"
CHECKED = {"review", "final", "posted"}
FINAL_COPY = ("article.md", "post.md", "page.md")
POST_WORD_LIMIT = 200  # the user's writing rules ({writing_overrides}, MY_WRITING_RULES.md), docs/channels.md
BLOG_WORD_LIMIT = 880  # a 4-minute read on the site (it counts 220 words a minute): the user's writing rules, set 2026-11-25
BLOG_LIMIT_FROM = "2026-11-25"  # the cap applies to blog posts started from this date (the content log's date column);
# the user exempted the posts written before it, which were all published by then: "apply this rule only for the future
# blogposts. previously posted ones can be ignored" (2026-11-25)
VOICE_LIBRARY = "tone-of-voice"  # workspace/tone-of-voice/: the user's own writing, kept as written, never checked


def is_voice_library(folder: str) -> bool:
    """True for a folder in the voice library (a path relative to workspace/, as the log writes it)."""
    return Path(folder).parts[:1] == (VOICE_LIBRARY,)


def log_rows(text: str) -> list[dict]:
    """Rows of the content log table: date, piece, channel, status (first word), folder."""
    rows = []
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not re.match(r"\d{4}-\d{2}-\d{2}", cells[0]):
            continue
        folder = re.search(r"`([^`]+)`", cells[4])
        status = re.match(r"[a-z]+", cells[3].lower())
        if folder:
            rows.append({"date": cells[0], "piece": cells[1], "channel": cells[2],
                         "status": status.group(0) if status else "", "folder": folder.group(1)})
    return rows


def unlogged_folders(rows: list[dict], pieces: Path | None = None) -> list[str]:
    """Piece folders under workspace/pieces/ that the content log does not list: nothing would check them."""
    pieces = pieces or LOG.parent / "pieces"
    logged = {Path(r["folder"]).name for r in rows}
    return sorted(f"{pieces.name}/{d.name}/" for d in pieces.iterdir() if d.is_dir() and d.name not in logged) if pieces.is_dir() else []


def piece_file(folder: Path) -> Path | None:
    for name in FINAL_COPY + ("draft.md",):
        if (folder / name).exists():
            return folder / name
    return None


def check_piece(row: dict, workspace: Path) -> tuple[Path | None, dict | None]:
    folder = workspace / row["folder"]
    path = piece_file(folder)
    if path is None:
        return None, None
    visuals = folder / "visuals.md"
    channel = row["channel"].lower()
    if "blog" in channel:
        max_words = BLOG_WORD_LIMIT if row["date"] >= BLOG_LIMIT_FROM else None
    else:
        max_words = POST_WORD_LIMIT if "post" in channel else None
    result = test_check_text.check(path.read_text(encoding="utf-8"), max_words,
                              visuals.read_text(encoding="utf-8") if visuals.exists() else None)
    structure = test_check_structure.check_folder(folder, row["channel"], row["status"])
    result["errors"] = result["errors"] + structure["errors"]
    result["warnings"] = result["warnings"] + structure["warnings"]
    return path, result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--all", action="store_true", help="check every piece in the log, whatever its status")
    args = ap.parse_args(argv)

    rows = log_rows(LOG.read_text(encoding="utf-8"))
    failed = 0
    for folder in unlogged_folders(rows):
        print(f"ERROR    {folder}: a piece folder with no row in workspace/content-log.md, so it would never be checked")
        failed += 1
    for row in rows:
        if is_voice_library(row["folder"]):
            print(f"skip     {row['folder']} (the voice library: the user's own writing, kept as written)")
            continue
        if not args.all and row["status"] not in CHECKED:
            print(f"skip     {row['folder']} ({row['status'] or 'no status'})")
            continue
        path, result = check_piece(row, LOG.parent)
        if path is None:
            print(f"ERROR    {row['folder']}: no article.md, post.md, page.md or draft.md")
            failed += 1
            continue
        label = path.relative_to(ROOT)
        if result["errors"]:
            failed += 1
            print(f"ERROR    {label}: {len(result['errors'])} error(s)")
            for e in result["errors"]:
                print(f"           {e}")
        else:
            print(f"ok       {label} ({result['words']} words)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
