#!/usr/bin/env python3
"""Keep restated rules tied to their source: every hard rule has one ID in house-rules.md, and copies name it.

Usage:
  python3 scripts/test_rule_sync.py FILE [FILE ...]     # scan files that restate house rules

house-rules.md ends each rule with its ID (`HR-no-dashes`). A file that restates a rule (this repo's
AGENTS.md and social voice rules, and the user's two voice guides)
names the ID in the same bullet or paragraph. The scan reports, per file:

  unknown    an ID the house rules no longer have: the source changed and this copy did not (error)
  uncited    a block that restates a rule, by its telltale words, without naming the ID (warning)
  untagged   a "No ..." rule with no ID at all: a rule that may exist only in this file (warning)

doctor.py runs the scan on the files listed under rule_mirrors: in config.yaml, so drift in the private
repo shows at session start, where CI cannot look. The tests run it on this repo's AGENTS.md.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOUSE_RULES = ROOT / "system" / "00-core" / "house-rules.md"
ID = re.compile(r"\bHR-[a-z0-9]+(?:-[a-z0-9]+)*\b")
RULE_LINE = re.compile(r"^- \*\*(.+?)\*\*.*`(HR-[a-z0-9-]+)`\s*$")
# Words that give away a restatement of a rule. Kept narrow: a mention that is not a restatement
# (a file name, a passing reference) should not need an ID.
SIGNALS = {
    "HR-never-invent": r"\bnever invent",
    "HR-mark-unknowns": r"\[CHECK:|\[YOUR MOMENT:",
    "HR-no-dashes": r"\bem (?:or en )?dash|\ben dash",
    "HR-no-negative-parallelism": r"negative parallelism|contrast formula",
    "HR-no-stock-phrasing": r"stock AI phrasing",
    "HR-no-lesson-reveal": r"taught me|lesson-reveal|lessons I learn",
    "HR-no-here-opener": r"\"Here(?:'s| is| are)\"",
    "HR-no-inflation": r"inflated significance|sound (?:more|bigger) important|made to sound more important",
    "HR-no-obvious": r"statements? of the obvious",
    "HR-no-slogans": r"\bslogans?\b",
    "HR-no-cinematic-openings": r"staccato|montage|cinematic",
    "HR-no-i-we-titles": r"starts? with \"I\"",
    "HR-no-sweeping-words": r"sweeping words?",
    "HR-no-explaining-down": r"explaining down|in plain words|in simple terms",
    "HR-describe-not-sell": r"sales adjectives?|promised outcomes?|sales pitch",
    "HR-no-launch-register": r"launch register|excited to share|proud to announce",
    "HR-voice-posts": r"\bCV verbs?\b|spearheaded",
    "HR-ai-no-significance-claims": r"significance claims?|legacy claims?",
    "HR-ai-vocabulary-density": r"AI vocabulary",
    "HR-ai-no-chat-residue": r"chatbot (?:talk|residue)",
    "HR-ai-no-template-blanks": r"template blanks?",
}
UNTAGGED_RULE = re.compile(r"^\s*(?:[-*]\s+)?\*\*No\s[^*]+\*\*")


def house_rule_ids(text: str | None = None) -> dict[str, str]:
    """{ID: bold rule name} from house-rules.md."""
    text = HOUSE_RULES.read_text(encoding="utf-8") if text is None else text
    return {m.group(2): m.group(1) for m in map(RULE_LINE.match, text.splitlines()) if m}


def blocks(text: str) -> list[tuple[int, str]]:
    """Paragraphs, list items and table rows, each with its first line number."""
    out: list[tuple[int, str]] = []
    current: list[str] = []
    start = 0
    for n, line in enumerate(text.splitlines(), 1):
        new_item = re.match(r"^\s*(?:[-*]\s|\d+\.\s|\|)", line)
        if not line.strip() or new_item:
            if current:
                out.append((start, " ".join(current)))
            current = []
        if line.strip():
            if not current:
                start = n
            current.append(line.strip())
    if current:
        out.append((start, " ".join(current)))
    return out


def scan(text: str, known: dict[str, str] | None = None) -> dict[str, list[str]]:
    known = house_rule_ids() if known is None else known
    report: dict[str, list[str]] = {"unknown": [], "uncited": [], "untagged": []}
    for n, block in blocks(text):
        cited = set(ID.findall(block))
        for rid in sorted(cited - set(known)):
            report["unknown"].append(f"line {n}: {rid} is not in house-rules.md (renamed or removed there?)")
        for rid, pattern in SIGNALS.items():
            m = re.search(pattern, block, re.I)
            if m and rid not in cited:
                report["uncited"].append(f"line {n}: restates {rid} ('{m.group(0)}') without naming it")
        if UNTAGGED_RULE.match(block) and not cited:
            report["untagged"].append(f"line {n}: a rule with no HR- ID, missing from house-rules.md or not tagged: {block[:70]}")
    return report


def main(argv: list[str] | None = None) -> int:
    paths = [Path(a) for a in (sys.argv[1:] if argv is None else argv)]
    if not paths:
        print(__doc__)
        return 2
    known = house_rule_ids()
    failed = False
    for path in paths:
        report = scan(path.read_text(encoding="utf-8"), known)
        failed |= bool(report["unknown"])
        print(f"{path}: {len(report['unknown'])} unknown, {len(report['uncited'])} uncited, {len(report['untagged'])} untagged")
        for kind in ("unknown", "uncited", "untagged"):
            for item in report[kind]:
                print(f"  {kind:9} {item}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
