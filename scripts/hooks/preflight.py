#!/usr/bin/env python3
"""SessionStart hook: check that the harness itself works before the session relies on it, and say so out loud.

Every other hook in this repo exits 0 when it breaks (a broken guard must not break the session) and reports on
stderr, which nobody reads. So a hook that cannot import, a sibling repo that went missing or a Python that is too
old would switch a guard off without a word. This hook runs first and checks:

  python     the interpreter the hooks run with is new enough for the scripts (MIN_PYTHON)
  hooks      every hook module and the scripts they import load, and the prompt hook answers
  doctor     scripts/doctor.py finds the sibling repos, the private files and the writing rules (exit 0)
  reviewer   whether the AI reviewer is calibrated, and how many rewrite pairs wait for a label (notes, not failures)

A failure becomes a systemMessage, which Claude Code shows the user, and context that tells the session what will
not work. When everything passes it adds one line of context and shows nothing. It never raises: a crash of its own
is reported the same way. Wired in .claude/settings.json, before the voice hook. Standard library only.
"""
from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
MIN_PYTHON = (3, 9)
MODULES = ("test_check_content", "protect_rules", "load_voice", "pairs", "test_check_text", "test_check_pieces",
           "ai_patterns", "ai_review", "doctor")


def check_python(version=sys.version_info) -> list[str]:
    if tuple(version[:2]) < MIN_PYTHON:
        return [f"python3 is {version[0]}.{version[1]}; the hooks need {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer "
                f"({sys.executable})"]
    return []


def check_hooks() -> list[str]:
    for d in (ROOT / "scripts", ROOT / "scripts" / "hooks"):
        if str(d) not in sys.path:
            sys.path.insert(0, str(d))
    problems = []
    for name in MODULES:
        try:
            importlib.import_module(name)
        except Exception as exc:  # any import failure switches a guard off
            problems.append(f"{name}.py does not load: {type(exc).__name__}: {exc}")
    if "test_check_content" in sys.modules:
        try:
            out = sys.modules["test_check_content"].decide_prompt({})
            if "test_check_text.py" not in json.dumps(out):
                problems.append("the prompt hook gave no reminder")
        except Exception as exc:
            problems.append(f"the prompt hook fails: {type(exc).__name__}: {exc}")
    return problems


def check_doctor(run=subprocess.run) -> list[str]:
    try:
        proc = run([sys.executable, str(ROOT / "scripts" / "doctor.py")], cwd=ROOT, capture_output=True, text=True,
                   timeout=8)
    except Exception as exc:
        return [f"doctor.py did not run: {type(exc).__name__}: {exc}"]
    if proc.returncode == 0:
        return []
    lines = [l.strip() for l in (proc.stdout + proc.stderr).splitlines()
             if l.strip() and not l.strip().startswith(("ok", "uncited"))]
    return ["doctor.py found a problem: " + "; ".join(lines[:4])]


def notes() -> list[str]:
    out = []
    try:
        ai_review = sys.modules.get("ai_review") or importlib.import_module("ai_review")
        out.append(f"AI reviewer: {ai_review.calibration_status()}")
    except (Exception, SystemExit) as exc:  # backend() exits on an unknown REVIEWER_BACKEND
        out.append(f"AI reviewer: status not read ({exc})")
    try:
        pairs = sys.modules.get("pairs") or importlib.import_module("pairs")
        waiting = len(pairs.unlabelled(ROOT))
        if waiting:
            out.append(f"{waiting} rewrite pair(s) wait for a label: python3 scripts/pairs.py list --unlabelled")
    except (Exception, SystemExit):
        pass
    return out


def decide(problems: list[str], extra: list[str]) -> dict:
    if not problems:
        context = "Harness preflight passed (python, hooks, doctor)." + "".join(f" {n}." for n in extra)
        return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}
    shown = "; ".join(problems[:3]) + (f" (+{len(problems) - 3} more)" if len(problems) > 3 else "")
    context = ("The harness preflight failed, so some guards in this repo may be off this session: "
               + "; ".join(problems) + ". Tell the user in one line before other work, check by hand what a broken "
               "hook would have checked (docs/running-from-outside.md lists it), and fix the cause when asked."
               + "".join(f" {n}." for n in extra))
    return {"systemMessage": f"content-ops-harness preflight failed: {shown}",
            "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}


def main() -> int:
    try:
        sys.stdin.read()
    except Exception:
        pass
    try:
        problems = check_python() + check_hooks() + check_doctor()
        out = decide(problems, notes())
    except (Exception, SystemExit) as exc:  # the one hook that must not fail quietly
        out = decide([f"preflight.py crashed: {type(exc).__name__}: {exc}"], [])
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
