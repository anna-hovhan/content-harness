#!/usr/bin/env python3
"""Claude Code PreToolUse hook: ask the user before any change to the files that hold the writing rules.

Reads the hook payload on stdin. For Edit, Write, MultiEdit and NotebookEdit it checks the target path;
for Bash it looks for a protected file named in a command that writes (sed -i, a redirect, tee, mv, cp,
rm, a Python write, git checkout or restore). Running the checkers themselves is not a write.
A match returns permissionDecision "ask" with the reason; anything else passes silently.
Wired in .claude/settings.json. CI's rules lock (tests/test_rules_lock.py) is the backstop.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

PROTECTED = (
    "system/00-core/house-rules.md",
    "system/00-core/banned-phrases.txt",
    "scripts/test_check_text.py",
    "scripts/test_check_pieces.py",
    "scripts/test_check_structure.py",
    "scripts/ai_patterns.py",
    "scripts/hooks/test_check_content.py",
    "tests/test_ai_patterns.py",
    "tests/test_content_hooks.py",
    "scripts/test_rule_sync.py",
    "scripts/ai_review.py",
    "scripts/test_calibrate_reviewer.py",
    "system/00-core/test_review-rubric.md",
    "tests/test_ai_review.py",
    "tests/feedback/calibration.json",
    ".github/workflows/ai-review.yml",
    "scripts/hooks/protect_rules.py",
    "tests/rules.lock",
    "tests/test_rules_lock.py",
    "tests/test_feedback_cases.py",
    "tests/test_guardrails.py",
    "tests/feedback/cases.json",
    "tests/feedback/pairs.json",
    "tests/feedback/synthetic.json",
    "tests/feedback/posts-left-out.json",
    "tests/feedback/calibration-synthetic.json",
    "scripts/pairs.py",
    "scripts/hooks/preflight.py",
    "tests/test_pairs.py",
    "tests/test_chat_and_preflight.py",
    "AGENTS.md",
    ".claude/settings.json",
    ".github/workflows/checks.yml",
)
# Running a checker reads it; it does not change it.
RUNS_A_CHECKER = re.compile(r"python3?\s+(?:-\S+\s+)*\S*(?:test_check_text|test_check_pieces|test_check_structure|test_rule_sync|ai_review|test_calibrate_reviewer|test_check_content|preflight)\.py"
    r"|python3?\s+(?:-\S+\s+)*\S*pairs\.py\s+(?:feedback|list)\b")
# A label that takes a pair out of calibration is the user's call: it asks, like an edit of pairs.json.
SKIPS_A_PAIR = re.compile(r"pairs\.py\s+label\b[^\n;&|]*--skip")
WRITES = re.compile(
    r"\bsed\s+(?:-\w*i|--in-place)|\bperl\s+-\w*i|(?<![0-9&>])>>?\s*(?!&|/dev/null)\S|\btee\b|\bmv\b|\bcp\b|\brm\b"
    r"|\btruncate\b|\bdd\b|\bpatch\b|write_text|\.write\(|open\([^)]*['\"][wax]|json\.dump\b"
    r"|\bgit\s+(?:checkout|restore|reset|stash|apply|am|cherry-pick|revert|rm|mv)\b"
)


def protected_target(path: str, root: Path) -> str | None:
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = root / p
    try:
        rel = p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None
    return rel if rel in PROTECTED else None


def protected_in_command(command: str) -> str | None:
    if SKIPS_A_PAIR.search(command):
        return "tests/feedback/pairs.json"
    rest = RUNS_A_CHECKER.sub(" ", command)
    named = [f for f in PROTECTED
             if f in rest or re.search(r"(?<![\w.-])" + re.escape(Path(f).name) + r"(?![\w-])", rest)]
    return named[0] if named and WRITES.search(rest) else None


def decide(payload: dict) -> dict | None:
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
    tool = payload.get("tool_name", "")
    data = payload.get("tool_input") or {}
    if tool == "Bash":
        hit = protected_in_command(data.get("command", ""))
    else:
        hit = protected_target(data.get("file_path") or data.get("notebook_path") or "", root)
    if not hit:
        return None
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": (
            f"{hit} holds the writing rules or the checks that enforce them. Changes need the user's yes "
            "(AGENTS.md, protected rule files). If this change is right, it must update tests/rules.lock too."),
    }}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    out = decide(payload)
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
