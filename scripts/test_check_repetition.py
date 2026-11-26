#!/usr/bin/env python3
"""Flag repeated ideas and reference-level detail in a draft.

Usage:
  python3 scripts/test_check_repetition.py <draft.md>

Two things the wording checks of test_check_text.py cannot see:

  * the same idea said in more than one place: paragraph pairs that share most of their content words,
    and a content-word pair (for example "shared context") that recurs in many paragraphs;
  * detail a reader can get from the repo: many backticked commands, skill and hook names.

Everything is a warning to read (exit 0): a thesis may return in the hook and the takeaway, and a term
may recur on purpose. The fix is to say each idea once, in the section it belongs to.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

STOP = set("""about above after again against also among because before being between both could does doing down during each
either every from further have having here herself himself into itself just more most much must myself once only other
ourselves over same should some such than that their theirs them themselves then there these they this those through
under until very were what when where which while whom will with would your yours yourself yourselves and are but can
for had has its not our out the you was who how why any all off own too use used uses using""".split())
WORD = re.compile(r"[a-z][a-z'-]+")
PAIR_JACCARD = 0.20       # paragraph pair overlap that reads as the same point
MIN_WORDS = 14            # shorter paragraphs are skipped
RECURRING_IN = 4          # a content-word pair in this many paragraphs is a theme said too often
CODE_TERMS_MAX = 5        # backticked terms before the draft reads as documentation


def stem(w: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def paragraphs(text: str) -> list[tuple[int, str]]:
    out, buf, start = [], [], 0
    for n, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("[IMAGE") or s.startswith("\\[IMAGE"):
            if buf:
                out.append((start, " ".join(buf)))
                buf = []
            continue
        if not buf:
            start = n
        buf.append(s)
    if buf:
        out.append((start, " ".join(buf)))
    return out


def content(par: str) -> list[str]:
    par = re.sub(r"`[^`]*`", " ", par)
    return [stem(w) for w in WORD.findall(par.lower()) if w not in STOP and len(w) > 3]


def check(text: str) -> list[str]:
    msgs = []
    pars = paragraphs(text)
    sets = {n: set(content(p)) for n, p in pars}
    lens = {n: len(p.split()) for n, p in pars}
    for (a, _), (b, _) in combinations(pars, 2):
        if lens[a] < MIN_WORDS or lens[b] < MIN_WORDS:
            continue
        inter = sets[a] & sets[b]
        union = sets[a] | sets[b]
        if union and len(inter) / len(union) >= PAIR_JACCARD and len(inter) >= 4:
            msgs.append(f"WARNING  lines {a} and {b} overlap ({', '.join(sorted(inter)[:6])}): the same point twice? Say it once.")
    names = {tuple(stem(w) for w in m.lower().split()) for m in re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", text)}
    where = defaultdict(set)
    for n, p in pars:
        w = content(p)
        for x, y in zip(w, w[1:]):
            if (x, y) in names:
                continue
            where[(x, y)].add(n)
    for (x, y), ns in sorted(where.items(), key=lambda kv: -len(kv[1])):
        if len(ns) >= RECURRING_IN:
            msgs.append(f"WARNING  '{x} {y}' recurs in {len(ns)} paragraphs (lines {', '.join(map(str, sorted(ns)))}): keep it where it earns its place.")
    codes = {c.lower() for c in re.findall(r"`([^`\n]+)`", text)}
    if len(codes) > CODE_TERMS_MAX:
        msgs.append(f"WARNING  {len(codes)} backticked terms: the repo documents commands, skills and hooks; keep only those the argument needs.")
    return msgs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file")
    args = ap.parse_args()
    msgs = check(Path(args.file).read_text(encoding="utf-8"))
    print(f"{args.file}: {len(msgs)} repetition warning(s)")
    for m in msgs:
        print("  " + m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
