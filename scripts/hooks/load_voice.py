#!/usr/bin/env python3
"""SessionStart hook: put the user's social voice guide into the session's context.

The voice guide (`social_voice` in writing-rules.yaml, in this repo's workspace/tone-of-voice/social/) is the one
description of how the user writes posts, articles and other text in their social voice (house rule
HR-voice-guide-first). Workflows used to tell the agent to read it, and it was skipped; this hook loads it at the
start of every session, and again after a resume, a clear or a compaction, so it does not depend on a step being
followed. The guide is in this repo, so the hook finds it in any clone or worktree.

Claude Code caps the context one hook adds at 10,000 characters (CAP). Past the cap Claude gets a preview
of the first 2,000 characters and a file path it is not told to read, so the output is kept under BUDGET,
header included. The guide is longer than that. Two kinds of section are left out, and the header names both:

- SKIP: the sections only a full post or article needs while drafting. The workflows read them from the file.
- Sections cut for size, in file order, whole: the header tells the session to read them from the file
  before writing anything in the user's voice, since a one-line request needs them too.

A guide that is missing, empty or unreadable is reported in the context, never silently skipped.

Wired in .claude/settings.json. Prints one JSON object for Claude Code and exits 0.
Documentation: docs/voice.md.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # scripts/, where doctor.py is; guide_path imports it

# Sections read from the file while drafting a full post or article, not needed in every session.
SKIP = ("Images", "Techniques I borrow")
CAP = 10000  # Claude Code's limit on one hook's additionalContext
BUDGET = 9900  # header and guide together; the margin is for anything Claude Code counts that this script cannot see


def size(text: str) -> int:
    """Length as Claude Code counts it: UTF-16 code units, so an emoji counts as two."""
    return len(text.encode("utf-16-le")) // 2


def project_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(env) if env else HERE.parent.parent


def guide_path(root: Path) -> Path | None:
    import doctor  # here, not at the top: main() then reports a doctor.py that fails to import, like any other failure

    config_file = root / "config.yaml"
    config = doctor.parse_config(config_file.read_text(encoding="utf-8")) if config_file.is_file() else {}
    paths = doctor.resolve(config, root)  # writing-rules.yaml (the contract) and config.yaml, as doctor.py reads them
    value = paths.get("social_voice")
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else root / path  # the repo's paths are relative to the repo, not the cwd


def sections(text: str) -> list[tuple[str, str]]:
    """Split on level-2 headings: [(heading, block)], the first heading empty for the preamble."""
    parts = re.split(r"(?m)^## (.*)$", text)
    out = [("", parts[0])]
    for i in range(1, len(parts), 2):
        out.append((parts[i].strip(), f"## {parts[i]}{parts[i + 1]}"))
    return out


def condense(text: str, limit: int) -> tuple[str, list[str], list[str]]:
    """The guide without the SKIP sections, and without the sections that do not fit in limit, each left out
    whole. A later section that still fits is kept. Returns text, skipped, cut."""
    kept, skipped, cut, used = [], [], [], 0
    for heading, block in sections(text):
        if heading and heading.startswith(SKIP):
            skipped.append(heading)
        elif used + size(block) > limit:
            cut.append(heading or "(opening)")
        else:
            kept.append(block)
            used += size(block)
    return "".join(kept).strip(), skipped, cut


def header(path: Path, skipped: list[str], cut: list[str]) -> str:
    text = (f"The user's social voice guide, loaded at session start from {path} by scripts/hooks/load_voice.py "
            "(house rule HR-voice-guide-first, docs/voice.md). It is the one description of how the user writes "
            "posts, articles, comments, replies and other text in their social voice: draft from it, and match its "
            "lines the user picked and turned down. Their published posts are what it is built from; do not read them "
            "for each piece. CVs and cover letters follow their own wording rules (cv_rules, cover_letter_rules) "
            "instead. The user's own rules (writing_overrides for writing, MY_RULES.md for confidentiality) and the "
            "house rules' hard rules win over it, in the order the house rules' opening paragraph sets.")
    if cut:
        text += (" The guide is longer than the hook's size limit, so these sections are missing below. Read them from "
                 "the file before writing anything in the user's voice, even one line: " + "; ".join(cut) + ".")
    if skipped:
        text += (" Left out here, read from the file when drafting a full post or article: "
                 + "; ".join(skipped) + ".")
    return text


def render(text: str, path: Path) -> str:
    """The header and as much of the guide as fits in BUDGET together. The header grows with every section it
    names as left out, so the room for the guide is measured on the finished text, not assumed."""
    limit = BUDGET
    while True:
        body, skipped, cut = condense(text, limit)
        out = header(path, skipped, cut) + "\n\n" + body
        over = size(out) - BUDGET
        if over <= 0:
            return out
        if not body:  # the header alone is over: more section names than fit
            return out[:BUDGET // 2].rstrip() + " [list cut short: read the whole guide from the file]"
        limit -= over


def context(root: Path) -> str:
    path = guide_path(root)
    if path is None or not path.is_file():
        where = path or "the social_voice entry in writing-rules.yaml"
        return ("The user's social voice guide was not found (" + str(where) + "). Before writing anything in the "
                "user's voice, tell the user it is missing (house rule HR-voice-guide-first). It is social_voice in "
                "writing-rules.yaml, a file in this repo: python3 scripts/doctor.py shows where it is looked for. "
                "When it was never built, \"Refresh my social voice\" builds it from the user's posts "
                "(/add-voice-sample, system/00-core/voice-library.md).")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return ("The user's social voice guide is empty (" + str(path) + "). Before writing anything in the user's "
                "voice, tell the user: the guide is built with \"Refresh my social voice\" "
                "(/add-voice-sample, system/00-core/voice-library.md) (house rule HR-voice-guide-first).")
    return render(text, path)


def main() -> int:
    try:
        sys.stdin.read()
        text = context(project_root())
    except Exception as exc:  # a broken loader must not break the session, and Claude never sees stderr on exit 0
        why = f"{type(exc).__name__}: {exc}"[:300]
        print(f"load_voice.py: {why}", file=sys.stderr)
        text = ("The user's social voice guide could not be loaded at session start (scripts/hooks/load_voice.py, "
                + why + "). Before writing anything in the user's voice, tell the user and read the guide from the "
                "file: the social_voice entry in writing-rules.yaml (house rule HR-voice-guide-first).")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
