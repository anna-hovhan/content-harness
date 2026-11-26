#!/usr/bin/env python3
"""Check that a piece folder went through the content loop (docs/mental-model.md), not only that its text is clean.

Usage:
  python3 scripts/test_check_structure.py PIECE_FOLDER [--channel "LinkedIn article"] [--status review] [--json]

test_check_pieces.py runs it on every piece in review, final or posted, with the channel and status from the
content log. Errors (exit 1):

  brief         brief.md is missing, or has no filled-in reader (who and their question), takeaway or terms table
  evidence      evidence.md is missing, or its facts table has no row with a source
  trace         a number in the piece is in no row of the evidence ledger
  links         a link in the piece is not in the ledger's links table, or a links row has no check date
  limits        a LinkedIn article or portfolio page has no limits or trade-offs section (a blog post needs none)
  status        the brief's status and the content log's status differ
  open marker   a [CHECK], [YOUR MOMENT] or [TODO] marker is left in a piece marked final or posted

Warnings (exit 0): a code identifier (`like_this`) that the ledger does not mention, and open markers in a
piece still in review. Tracing is literal on purpose: it proves the ledger was built and kept, and leaves
"does the ledger row say what the sentence says" to the reader and the AI reviewer.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FINAL_COPY = ("article.md", "post.md", "page.md")
NEEDS_LIMITS = ("article", "portfolio")  # channels whose arc has a trade-offs and limits beat
LIMITS_HEADING = re.compile(r"^#{2,4}\s+.*\b(limit|limits|limitations|trade-?offs?|caveats?(?![\w-])|where (it|this) (stops|breaks))\b", re.I | re.M)
PLACEHOLDER = re.compile(r"^\s*\[[^\]]*\]\s*$")
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
OPEN_MARKER = re.compile(r"\[(CHECK:|YOUR MOMENT:|TODO)[^\]]*\]")
IMAGE_MARKER = re.compile(r"^\s*\[IMAGE\s+v\d+\s*:[^\]]*\]\s*$", re.M)
# Numbers written with digits: 32, 2026-11-10, 1,281, 4.5, 80%. Version tags like v2 belong to markers.
NUMBER = re.compile(r"(?<![\w.])\d[\d,.:%-]*\d%?(?![\w])|(?<![\w.])\d%?(?![\w.,-]?\w)")
URL = re.compile(r"(?:https?://)?(?:www\.)?((?:[a-z0-9-]+\.)+(?:com|org|io|ai|dev|net|co|app|so|me|nl|eu)(?:/[^\s)\]>*`'\",]*)?)", re.I)
CODE = re.compile(r"`([^`\n]+)`")
IDIOM = re.compile(r"\b1:1s?\b")  # a meeting type, not a number to trace
STATUSES = ("idea", "drafting", "review", "final", "posted", "parked")


def section(text: str, heading: str) -> str:
    """The body under the first '## <heading>...' up to the next heading of the same level."""
    m = re.search(rf"^##\s+{re.escape(heading)}\b.*$", text, re.I | re.M)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^##\s", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def table_rows(text: str) -> list[list[str]]:
    """Data rows of the markdown tables in text (header and separator rows dropped)."""
    rows, header_seen = [], False
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            header_seen = False
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            header_seen = True
            continue
        if header_seen:
            rows.append(cells)
    return rows


def filled(value: str) -> bool:
    value = value.strip()
    return bool(value) and not PLACEHOLDER.match(value) and value.lower() not in {"none", "n/a", "-"}


def brief_status(brief: str) -> str:
    m = re.search(r"^\*\*Status:\*\*\s*([a-z]+)", brief, re.I | re.M)
    return m.group(1).lower() if m else ""


def normalise_url(url: str) -> str:
    return re.sub(r"^(https?://)?(www\.)?", "", url.lower()).rstrip("/.")


def piece_body(text: str) -> str:
    """The piece without image markers and HTML comments, which carry no facts."""
    return IMAGE_MARKER.sub("", re.sub(r"<!--.*?-->", "", text, flags=re.S))


def check(brief: str | None, evidence: str | None, piece: str, channel: str = "",
          log_status: str | None = None) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    body = piece_body(piece)

    # Frame: reader, takeaway, terms table.
    if brief is None:
        errors.append("brief: no brief.md")
    else:
        reader = section(brief, "Reader")
        who = re.search(r"\*\*Who\b[^*]*:\*\*\s*(.+)", reader)
        question = re.search(r"\*\*Their question\b[^*]*:\*\*\s*(.+)", reader)
        if not (who and filled(who.group(1))):
            errors.append("brief: the reader has no 'Who' line, or it is still a placeholder")
        if not (question and filled(question.group(1))):
            errors.append("brief: the reader has no 'Their question' line, or it is still a placeholder")
        takeaway = [l for l in section(brief, "Takeaway").splitlines() if l.strip()]
        if not takeaway or not filled(takeaway[0]):
            errors.append("brief: no takeaway sentence")
        terms = [r for r in table_rows(section(brief, "Terms table")) if len(r) >= 2 and filled(r[0]) and filled(r[1])]
        if not terms:
            errors.append("brief: the terms table has no filled-in row")
        status = brief_status(brief)
        if log_status is not None and status != log_status:
            errors.append(f"status: the brief says '{status or 'no status'}', the content log says '{log_status}'")

    # Gather: the ledger, facts traced to it, links checked.
    if evidence is None:
        errors.append("evidence: no evidence.md")
    else:
        facts = [r for r in table_rows(section(evidence, "Facts")) if len(r) >= 3 and filled(r[1]) and filled(r[2])]
        if not facts:
            errors.append("evidence: the facts table has no row with a claim and a source")
        # Claims and sources only: the row numbers in the # column would trace any small number.
        ledger_text = " ".join(" ".join(r[1:3]) for r in table_rows(section(evidence, "Facts")) if len(r) >= 3)
        ledger_numbers = set(NUMBER.findall(ledger_text))
        for num in sorted(set(NUMBER.findall(IDIOM.sub(" ", body)))):
            if num not in ledger_numbers:
                errors.append(f"trace: the number '{num}' is in no row of the evidence ledger")
        ledger_lower = evidence.lower()
        for ident in sorted(set(CODE.findall(body))):
            if ident.lower() not in ledger_lower:
                warnings.append(f"trace: `{ident}` is not mentioned in the evidence ledger")
        links = table_rows(section(evidence, "Links the piece may use"))
        listed = set()
        for row in links:
            if not filled(row[0]):
                continue
            listed.add(normalise_url(URL.search(row[0]).group(1) if URL.search(row[0]) else row[0]))
            if not (len(row) >= 3 and DATE.search(row[2])):
                errors.append(f"links: '{row[0]}' has no check date in the links table")
        for m in URL.finditer(body):
            url = normalise_url(m.group(1))
            if "/" not in url and "." in url and url.count(".") == 1 and url.split(".")[0] in {"readme", "roadmap", "claude", "agents"}:
                continue  # a file name such as ROADMAP.md, not a link
            if not any(url == l or url.startswith(l + "/") or l.startswith(url) for l in listed):
                errors.append(f"links: '{m.group(0)}' is not in the evidence ledger's links table")

    # Shape: articles and portfolio pages carry their limits. A blog post need not, whatever its date: the user's writing
    # rules keep its limits to a sentence or two, or none (set 2026-11-25), and removing a limits section from an older
    # post is allowed under them; only the word cap is limited to posts from that date.
    if any(c in channel.lower() for c in NEEDS_LIMITS) and "blog" not in channel.lower() and not LIMITS_HEADING.search(body):
        errors.append("limits: no limits or trade-offs section (a heading naming limits, limitations or trade-offs)")

    # Check: nothing open in a piece the user approved.
    for m in OPEN_MARKER.finditer(body):
        if log_status in ("final", "posted"):
            errors.append(f"open marker: {m.group(0)[:60]} in a piece marked {log_status}")
        else:
            warnings.append(f"open marker: {m.group(0)[:60]}")
    return {"errors": errors, "warnings": warnings}


def piece_file(folder: Path) -> Path | None:
    for name in FINAL_COPY + ("draft.md",):
        if (folder / name).exists():
            return folder / name
    return None


def check_folder(folder: Path, channel: str = "", log_status: str | None = None) -> dict:
    def read(name: str) -> str | None:
        p = folder / name
        return p.read_text(encoding="utf-8") if p.exists() else None

    path = piece_file(folder)
    if path is None:
        return {"errors": ["no article.md, post.md, page.md or draft.md"], "warnings": []}
    return check(read("brief.md"), read("evidence.md"), path.read_text(encoding="utf-8"), channel, log_status)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("folder", type=Path)
    ap.add_argument("--channel", default="")
    ap.add_argument("--status", choices=STATUSES)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    result = check_folder(args.folder, args.channel, args.status)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for e in result["errors"]:
            print(f"ERROR    {e}")
        for w in result["warnings"]:
            print(f"warning  {w}")
        if not result["errors"]:
            print("ok")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
