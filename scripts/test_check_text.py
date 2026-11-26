#!/usr/bin/env python3
"""Check a draft against the house rules.

Errors (exit 1): em or en dashes, banned phrases, negative parallelism, lesson-reveal framing, number-pair slogans ("1 folder, 3 commands"),
titles or headings that start with "I" or "We", montages of sentence fragments, staccato runs of short sentences,
sentences starting with "Here is" / "Here's" / "Here are",
word limit exceeded, image markers that do not match the placement map, and the AI-writing-pattern rules
(house-rules.md, section 2.2; scripts/ai_patterns.py): significance claims, chatbot talk, stock headings, template blanks,
markdown in a LinkedIn post and so on, each naming its HR-ai- rule. An AI-pattern score under 70 is an error too.
Warnings (exit 0): open [CHECK: ...], [YOUR MOMENT: ...], [TODO ...] markers, TBD, two short
fragments in a row that read like a slogan, and the AI patterns that are wrong only in a cluster (they cost points in the score).

Usage:
  python3 scripts/test_check_text.py DRAFT.md [--max-words N] [--visuals VISUALS.md] [--channel NAME] [--json]
  printf '%s' "text" | python3 scripts/test_check_text.py -      # any text, no file needed

Word count: when the draft has a "## Post" section, only that section is counted
(hook to close, as the user's writing rules, {writing_overrides}, define it). Otherwise the whole draft is counted.
Image markers, headings, markdown syntax and HTML comments are not counted.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_patterns  # noqa: E402
import test_check_repetition  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BANNED_FILE = ROOT / "system" / "00-core" / "banned-phrases.txt"

DASHES = {"\u2014": "em dash", "\u2013": "en dash"}
MARKER_RE = re.compile(r"^\s*\[IMAGE\s+(v\d+)\s*:\s*([^\]]+?)\s*\]\s*$")
OPEN_MARKERS = [
    (re.compile(r"\[CHECK:[^\]]*\]"), "open [CHECK] marker"),
    (re.compile(r"\[YOUR MOMENT:[^\]]*\]"), "open [YOUR MOMENT] marker"),
    (re.compile(r"\[TODO[^\]]*\]"), "open [TODO] marker"),
    (re.compile(r"\bTBD\b"), "TBD"),
]
# Negative parallelism and contrast formulas (social-voice-rules.md, section 2).
PARALLELISM = [
    re.compile(r"\b(it|this|that)(\s+i|')s\s+not\s+[^.?!]{1,60}?[,;.]\s*(it|this|that)(\s+i|')s\b", re.I),
    re.compile(r"\b(isn't|is not|aren't|are not)\s+just\b", re.I),
    re.compile(r"\bnot because\b[^.?!]{1,80}\bbut because\b", re.I),
    re.compile(r"\bless\s+\w+,\s*more\s+\w+", re.I),
    re.compile(r",\s*not just\b", re.I),
]
# A sentence that starts with "Here is", "Here's" or "Here are", including titles, headings,
# list items and quotes (house-rules.md, section 2).
HERE_START = re.compile(
    r"(?:^\s*(?:#+\s+|[-*>]\s+|\d+\.\s+)?|[.!?:]\s+)[*_\"'\u201c\u2018(]*(?:(?:and|but|so|now|then|well|ok|okay),?\s+)?here(?:['\u2019]s|\s+is|\s+are)\b", re.I)
# Slogans (house-rules.md, section 2): number pairs like "1 folder, 3 commands" are errors;
# two short verbless-looking fragments in a row ("Private by default. Shared on purpose.") are warnings.
_NUM = r"(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)"
NUMBER_PAIR = re.compile(r"\b" + _NUM + r"\s+[a-z][\w'-]*,\s*" + _NUM + r"\s+[a-z][\w'-]*", re.I)
# A title or heading that opens with a counted noun and a comma: "One ask, the week files itself".
HEADING_NUM = re.compile(r"^\s*#+\s+" + _NUM + r"\s+[a-z][\w'-]*,", re.I)
SUBJECTS = {"i", "you", "we", "they", "it", "he", "she", "this", "that", "there", "nobody", "everyone"}


def fragment_pairs(line: str) -> list[str]:
    text = re.sub(r"^\s*(?:#+|[-*>]|\d+\.)\s+", "", line)
    text = re.sub(r"[*_`]", "", text)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    found = []
    for a, b in zip(sentences, sentences[1:]):
        if not (a.endswith(".") and b.endswith(".")):
            continue
        wa, wb = a.rstrip(".").split(), b.rstrip(".").split()
        if 2 <= len(wa) <= 4 and 2 <= len(wb) <= 4 and wa[0].lower() not in SUBJECTS and wb[0].lower() not in SUBJECTS:
            found.append(f"{a} {b}")
    return found


# Montage and staccato runs (house-rules.md, section 2). A fragment here is a sentence that opens with a
# determiner and has no auxiliary and no early -s verb: "The strategy deck." "The goal we agreed on in January."
# Three in a row is a montage (error). Three short sentences in a row is staccato (error).
DETERMINERS = {"the", "a", "an", "every", "each", "no", "our", "your", "my", "their", "his", "her", "its",
               "this", "that", "these", "those", "another"}
AUXILIARIES = {"is", "are", "was", "were", "be", "been", "being", "am", "has", "have", "had", "do", "does", "did",
               "can", "cannot", "could", "will", "would", "shall", "should", "may", "might", "must"}
SENTENCE_SPLIT = re.compile(r"(?:(?<=[.!?])|(?<=[.!?][\"'”’)]))\s+")
WORD = re.compile(r"[A-Za-z0-9][\w'’-]*")
MONTAGE_RUN = 3
STACCATO_RUN, STACCATO_WORDS = 3, 6
# A title or heading that opens with "I" or "We" reads as a launch announcement ("I built...", "I gave my company a brain").
PRONOUN_TITLE = re.compile(r"^\s*#+\s+[*_\"'“]*(?:i|we)(?:['’](?:m|ve|d|ll|re))?\b", re.I)


def sentences(line: str) -> list[str]:
    text = re.sub(r"^\s*(?:#+|[-*>]|\d+\.)\s+", "", line)
    text = re.sub(r"[*_`]", "", text)
    return [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]


def is_fragment(sentence: str) -> bool:
    words = [w.lower().replace("’", "'") for w in WORD.findall(sentence)]
    if not words or words[0] not in DETERMINERS:
        return False
    if any(w in AUXILIARIES or w.endswith("n't") for w in words):
        return False
    # an early word ending in -s is most likely the main verb ("The weekly skill pulls the week...")
    early = words[1:5]
    return not any(len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "'s", "us", "is")) for w in early)


def runs(items: list[bool], length: int) -> bool:
    count = 0
    for item in items:
        count = count + 1 if item else 0
        if count >= length:
            return True
    return False


# Lesson-reveal framing: "Here's what X taught me about Y", "What I learnt" (house-rules.md, section 2).
LESSON_REVEAL = [
    re.compile(r"\b(taught|teaches|teaching)\s+(me|us)\b", re.I),
    re.compile(r"\bwhat\s+(i|we)(\s+have|['\u2019]ve)?\s+(learnt|learned)\b", re.I),
    re.compile(r"\blessons?\s+(i|we)(\s+have|['\u2019]ve)?\s+(learnt|learned)\b", re.I),
]


def load_banned(path: Path = BANNED_FILE) -> list[str]:
    if not path.exists():
        return []
    phrases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            phrases.append(line.lower())
    return phrases


def phrase_pattern(phrase: str) -> re.Pattern:
    escaped = re.escape(phrase).replace("'", "['’]")
    start = r"\b" if phrase[0].isalnum() else ""
    end = r"\b" if phrase[-1].isalnum() else ""
    return re.compile(start + escaped + end, re.I)


def post_section(text: str) -> str | None:
    """Return the body of a '## Post' section, or None when there is none."""
    m = re.search(r"^##\s+Post\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return m.group(1) if m else None


def count_words(text: str) -> int:
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    words = 0
    for line in text.splitlines():
        if MARKER_RE.match(line) or line.lstrip().startswith("#"):
            continue
        line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)  # links: keep the text
        line = re.sub(r"[*_`>|]", " ", line)
        words += len(re.findall(r"[A-Za-z0-9À-ɏ][\w'’./:-]*", line))
    return words


def markers(text: str) -> dict[str, str]:
    found = {}
    for line in text.splitlines():
        m = MARKER_RE.match(line)
        if m:
            found[m.group(1)] = m.group(2)
    return found


def placement_rows(visuals_text: str) -> dict[str, str]:
    """Rows of the placement table: '| v1 | slug | ...'."""
    rows = {}
    for line in visuals_text.splitlines():
        m = re.match(r"^\|\s*(v\d+)\s*\|\s*([^|]+?)\s*\|", line)
        if m:
            rows[m.group(1)] = m.group(2).strip("` ")
    return rows


def check(text: str, max_words: int | None = None, visuals_text: str | None = None,
          banned: list[str] | None = None, channel: str | None = None) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    banned = load_banned() if banned is None else banned

    for n, line in enumerate(text.splitlines(), 1):
        for ch, name in DASHES.items():
            if ch in line:
                errors.append(f"line {n}: {name}: {line.strip()[:80]}")
        if MARKER_RE.match(line):
            continue
        for phrase in banned:
            if phrase_pattern(phrase).search(line):
                errors.append(f"line {n}: banned phrase '{phrase}'")
        for pat in PARALLELISM:
            m = pat.search(line)
            if m:
                errors.append(f"line {n}: contrast formula '{m.group(0)}'")
        m = NUMBER_PAIR.search(line) or HEADING_NUM.search(line)
        if m:
            errors.append(f"line {n}: slogan '{m.group(0)}'")
        for pair in fragment_pairs(line):
            warnings.append(f"line {n}: reads like a slogan, rewrite as a sentence if it is one: {pair[:80]}")
        if PRONOUN_TITLE.match(line):
            errors.append(f"line {n}: title or heading starts with 'I' or 'We': state the subject or the claim: {line.strip()[:80]}")
        sents = [] if line.lstrip().startswith("|") else sentences(line)  # table cells are not prose
        if runs([is_fragment(s) for s in sents], MONTAGE_RUN):
            errors.append(f"line {n}: montage of sentence fragments, open with the point in a full sentence: {line.strip()[:80]}")
        if runs([len(WORD.findall(s)) <= STACCATO_WORDS for s in sents], STACCATO_RUN):
            errors.append(f"line {n}: staccato run of {STACCATO_RUN} or more short sentences, join them: {line.strip()[:80]}")
        m = HERE_START.search(line)
        if m:
            errors.append(f"line {n}: sentence starts with '{m.group(0).strip()}'")
        for pat in LESSON_REVEAL:
            m = pat.search(line)
            if m:
                errors.append(f"line {n}: lesson-reveal framing '{m.group(0)}'")
        for pat, name in OPEN_MARKERS:
            for m in pat.finditer(line):
                warnings.append(f"line {n}: {name}: {m.group(0)[:80]}")

    section = post_section(text)
    words = count_words(section if section is not None else text)
    if max_words is not None and words > max_words:
        errors.append(f"{words} words, over the limit of {max_words}")

    found = markers(text)
    if visuals_text is not None:
        rows = placement_rows(visuals_text)
        for vid, slug in found.items():
            if vid not in rows:
                errors.append(f"marker [IMAGE {vid}: {slug}] has no row in the placement map")
            elif rows[vid] != slug:
                errors.append(f"marker {vid} says '{slug}', the placement map says '{rows[vid]}'")
        for vid, slug in rows.items():
            if vid not in found and not slug.startswith("["):
                errors.append(f"placement row {vid} ({slug}) has no [IMAGE {vid}: {slug}] marker in the draft")

    hits = ai_patterns.scan(text, channel)
    for h in hits:
        (errors if h["severity"] == ai_patterns.HARD else warnings).append(f"line {h['line']}: {h['message']}")
    result_score = ai_patterns.score(hits)
    if result_score["verdict"] == "fail" and not any(h["severity"] == ai_patterns.HARD for h in hits):
        errors.append(f"AI-pattern score {result_score['score']} is under {ai_patterns.FAIL_BELOW}: too many soft signs "
                      f"({', '.join(f'{r} {c}' for r, c in sorted(result_score['by_rule'].items(), key=lambda kv: -kv[1])[:4])}); rewrite the flagged passages")

    for m in test_check_repetition.check(text):
        warnings.append(m.replace("WARNING  ", "", 1))

    return {"words": words, "counted": "post section" if section is not None else "whole draft",
            "markers": found, "errors": errors, "warnings": warnings, "score": result_score}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("draft", type=Path, help="a file, or - for standard input")
    ap.add_argument("--channel", help="the channel, e.g. 'LinkedIn post': a post is checked for markdown it will not render")
    ap.add_argument("--max-words", type=int)
    ap.add_argument("--visuals", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    text = sys.stdin.read() if str(args.draft) == "-" else args.draft.read_text(encoding="utf-8")
    visuals_text = args.visuals.read_text(encoding="utf-8") if args.visuals else None
    result = check(text, args.max_words, visuals_text, channel=args.channel)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{args.draft}: {result['words']} words ({result['counted']}), "
              f"{len(result['markers'])} image marker(s)")
        s = result["score"]
        print(f"  AI-pattern score {s['score']}/100 ({s['verdict']})")
        for e in result["errors"]:
            print(f"  ERROR    {e}")
        for w in result["warnings"]:
            print(f"  WARNING  {w}")
        if not result["errors"]:
            print("  OK: no errors" + (" (open markers above are for the user)" if result["warnings"] else ""))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
