#!/usr/bin/env python3
"""Rewrite pairs: the agent's first version of a passage, which the user sent back with feedback, and the agent's
final version of it, which the user approved. They are the user's corrections in their own words, kept as labelled
data for the AI reviewer's calibration (scripts/test_calibrate_reviewer.py).

How a pair is made, with no step for the user:
  1. first   The first turn that ends with a piece in `review` (the user is about to read it) saves its copy files,
             once, to <piece>/.first/. The Stop hook does it (scripts/hooks/test_check_content.py), and only once
             the files pass the checks, so the snapshot is what the user saw. Pieces dated before SINCE are left
             out: they had feedback rounds before first versions were saved.
  2. rounds  Each round of the user's feedback goes to <piece>/feedback.md (`pairs.py feedback`), dated.
  3. final   When the piece reaches `final` or `posted` (the user approved it), the hook pairs the first version
             with the approved copy passage by passage: every passage the agent rewrote or cut becomes a pair in
             tests/feedback/pairs.json, with the piece's feedback.
  4. label   New pairs are unlabelled, and an unlabelled pair is left out of calibration. The agent labels each one
             from the feedback and the rubric: the criterion the first version broke, --any when it broke the
             user's taste in a way no criterion names, or --skip when the change was a fact or a content decision
             a reviewer cannot judge. The hook asks for the labels when it captures pairs.

Usage:
  python3 scripts/pairs.py feedback <piece> "<what the user said>"
  python3 scripts/pairs.py snapshot <piece>        # save the first version now (normally the Stop hook does it)
  python3 scripts/pairs.py capture <piece>         # pair first and final now (normally the Stop hook does it)
  python3 scripts/pairs.py label <pair id> (--criterion <id> | --any | --skip "<why>")
  python3 scripts/pairs.py list [--unlabelled]
<piece> is the folder name under workspace/pieces/ (2026-11-25-reply) or its path. Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import test_check_pieces  # noqa: E402

FIRST_DIR = ".first"
FEEDBACK_FILE = "feedback.md"
MAIN_COPY = test_check_pieces.FINAL_COPY + ("text.md", "draft.md")  # the piece's main copy, approved copy first
APPROVED = {"final", "posted"}
SNAPSHOT_AT = "review"
SINCE = "2026-11-25"  # pieces dated before this went through feedback before first versions were saved: left out
IMAGE_MARKER = re.compile(r"^\[IMAGE [^\]]*\]$")


def pairs_path(root: Path = ROOT) -> Path:
    return root / "tests" / "feedback" / "pairs.json"


def load(root: Path = ROOT) -> dict:
    path = pairs_path(root)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"_about": ("Rewrite pairs: the agent's first version of a passage, which the user sent back, and its final "
                       "version, which the user approved, captured by scripts/pairs.py. calibrate: null means not "
                       "labelled yet (left out of calibration), true means the reviewer must flag the first version "
                       "(under criterion when there is one) and pass the final, false means a change a reviewer "
                       "cannot judge (label_note says why)."),
            "pairs": []}


def save(doc: dict, root: Path = ROOT) -> None:
    path = pairs_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def piece_folder(piece: str, root: Path = ROOT) -> Path:
    p = Path(piece)
    folder = p if p.is_absolute() or p.exists() else root / "workspace" / "pieces" / piece.strip("/").split("/")[-1]
    if not folder.is_dir():
        raise SystemExit(f"no piece folder {folder}")
    return folder


def main_copy(folder: Path) -> Path | None:
    for name in MAIN_COPY:
        if (folder / name).exists():
            return folder / name
    return None


def passages(text: str) -> list[str]:
    """Paragraphs, headings and list blocks, split on blank lines; image markers and code fences left out."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    out = []
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if block and not IMAGE_MARKER.match(block):
            out.append(block)
    return out


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def rewrites(first: str, final: str) -> list[tuple[str, str]]:
    """(first, final) for each passage the agent rewrote or cut; a cut passage pairs with an empty final."""
    a, b = passages(first), passages(final)
    matcher = difflib.SequenceMatcher(None, [_norm(x) for x in a], [_norm(x) for x in b], autojunk=False)
    out = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "replace" and i2 - i1 == j2 - j1 and i2 - i1 > 1:
            # Several passages rewritten in a row, one for one: one pair each, so each gets its own label.
            out += [(x, y) for x, y in zip(a[i1:i2], b[j1:j2]) if _norm(x) != _norm(y)]
        elif op in ("replace", "delete"):
            before, after = "\n\n".join(a[i1:i2]), "\n\n".join(b[j1:j2])
            if _norm(before) != _norm(after):
                out.append((before, after))
        # A passage added at the user's request has no first version to flag, so it is not a pair.
    return out


def snapshot(folder: Path, today: str | None = None) -> bool:
    """Save the piece's main copy as its first version, once. False when one exists or there is no copy yet."""
    first = folder / FIRST_DIR
    copy = main_copy(folder)
    if (first / "meta.json").exists() or copy is None:
        return False
    first.mkdir(exist_ok=True)
    shutil.copy2(copy, first / copy.name)
    meta = {"file": copy.name, "date": today or dt.date.today().isoformat(), "captured": None}
    (first / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return True


def capture(folder: Path, root: Path = ROOT, today: str | None = None) -> list[dict]:
    """Pair the first version with the approved copy; returns the new pairs (none when already captured)."""
    meta_path = folder / FIRST_DIR / "meta.json"
    if not meta_path.exists():
        return []
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("captured"):
        return []
    final_file = main_copy(folder)
    first_file = folder / FIRST_DIR / meta["file"]
    if final_file is None or not first_file.exists():
        return []
    today = today or dt.date.today().isoformat()
    feedback_file = folder / FEEDBACK_FILE
    feedback = feedback_file.read_text(encoding="utf-8").strip() if feedback_file.exists() else ""
    doc = load(root)
    taken = {p["id"] for p in doc["pairs"]}
    new, n = [], 0
    for before, after in rewrites(first_file.read_text(encoding="utf-8"), final_file.read_text(encoding="utf-8")):
        n += 1
        while f"{folder.name}-{n}" in taken:
            n += 1
        pair = {"id": f"{folder.name}-{n}", "piece": folder.name, "date": today,
                "file": f"{meta['file']} -> {final_file.name}", "first": before, "final": after,
                "feedback": feedback, "criterion": None, "calibrate": None, "label_note": ""}
        doc["pairs"].append(pair)
        taken.add(pair["id"])
        new.append(pair)
    save(doc, root)
    meta["captured"] = today
    meta["pairs"] = len(new)
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return new


def log_rows(root: Path = ROOT) -> list[dict]:
    log = root / "workspace" / "content-log.md"
    return test_check_pieces.log_rows(log.read_text(encoding="utf-8")) if log.exists() else []


def snapshot_ready(root: Path = ROOT, is_clean=None) -> list[str]:
    """Snapshot every piece in review that has no first version yet. is_clean(path) can hold a snapshot back
    until the copy passes the checks, so the first version is the one the user reads."""
    done = []
    for row in log_rows(root):
        folder = root / "workspace" / row["folder"]
        if row["status"] != SNAPSHOT_AT or not folder.is_dir() or (folder / FIRST_DIR / "meta.json").exists():
            continue
        if row.get("date", "") < SINCE:
            continue  # its first version was never saved; today's text would pass for it and hide earlier rounds
        copy = main_copy(folder)
        if copy is None or (is_clean is not None and not is_clean(copy)):
            continue
        if snapshot(folder):
            done.append(folder.name)
    return done


def capture_ready(root: Path = ROOT) -> dict[str, int]:
    """Capture every approved piece that has a first version and no pairs yet: {piece: new pairs}."""
    out = {}
    for row in log_rows(root):
        folder = root / "workspace" / row["folder"]
        if row["status"] in APPROVED and folder.is_dir():
            meta = folder / FIRST_DIR / "meta.json"
            if meta.exists() and not json.loads(meta.read_text(encoding="utf-8")).get("captured"):
                out[folder.name] = len(capture(folder, root))
    return out


def unlabelled(root: Path = ROOT) -> list[dict]:
    return [p for p in load(root)["pairs"] if p.get("calibrate") is None]


def label(pair_id: str, criterion: str | None = None, any_finding: bool = False, skip: str | None = None,
          root: Path = ROOT) -> dict:
    doc = load(root)
    pair = next((p for p in doc["pairs"] if p["id"] == pair_id), None)
    if pair is None:
        raise SystemExit(f"no pair {pair_id!r}: python3 scripts/pairs.py list")
    if criterion:
        import ai_review
        known = ai_review.rubric_criteria()
        if criterion not in known:
            raise SystemExit(f"{criterion!r} is not a rubric criterion: {', '.join(known)}")
        pair.update(criterion=criterion, calibrate=True, label_note="")
    elif any_finding:
        pair.update(criterion=None, calibrate=True, label_note="the user's taste; no single criterion")
    elif skip:
        pair.update(criterion=None, calibrate=False, label_note=skip)
    else:
        raise SystemExit("give --criterion <id>, --any or --skip \"<why>\"")
    save(doc, root)
    return pair


def add_feedback(folder: Path, text: str, today: str | None = None) -> Path:
    path = folder / FEEDBACK_FILE
    head = "" if path.exists() else f"# Feedback on {folder.name}\n\nEach round of the user's feedback, as they gave it.\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"{head}\n## {today or dt.date.today().isoformat()}\n\n{text.strip()}\n")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("feedback")
    f.add_argument("piece")
    f.add_argument("text")
    sub.add_parser("snapshot").add_argument("piece")
    sub.add_parser("capture").add_argument("piece")
    lab = sub.add_parser("label")
    lab.add_argument("id")
    g = lab.add_mutually_exclusive_group(required=True)
    g.add_argument("--criterion")
    g.add_argument("--any", action="store_true")
    g.add_argument("--skip")
    ls = sub.add_parser("list")
    ls.add_argument("--unlabelled", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "feedback":
        print(f"recorded in {add_feedback(piece_folder(args.piece), args.text).relative_to(ROOT)}")
    elif args.cmd == "snapshot":
        folder = piece_folder(args.piece)
        print("first version saved" if snapshot(folder) else "a first version exists already, or there is no copy yet")
    elif args.cmd == "capture":
        new = capture(piece_folder(args.piece))
        print(f"{len(new)} new pair(s)" + (": label each with python3 scripts/pairs.py label <id> ..." if new else ""))
    elif args.cmd == "label":
        p = label(args.id, args.criterion, args.any, args.skip)
        print(f"{p['id']}: calibrate {p['calibrate']}, criterion {p['criterion'] or '-'}")
    else:
        rows = unlabelled() if args.unlabelled else load()["pairs"]
        for p in rows:
            state = "unlabelled" if p["calibrate"] is None else (p["criterion"] or ("any" if p["calibrate"] else "skip"))
            print(f"{p['id']:40} {state:16} first: {_norm(p['first'])[:70]}")
        if not rows:
            print("no pairs" + (" to label" if args.unlabelled else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
