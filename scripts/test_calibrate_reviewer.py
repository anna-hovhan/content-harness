#!/usr/bin/env python3
"""Calibrate the AI reviewer on the user's own judgments, and record the result for its fingerprint.

Usage:
  python3 scripts/test_calibrate_reviewer.py --dry-run           # what would run, and a cost estimate; no model call
  python3 scripts/test_calibrate_reviewer.py [--jobs 4]          # run it and write tests/feedback/calibration.json
  python3 scripts/test_calibrate_reviewer.py --set synthetic     # the smoke test: tests/feedback/calibration-synthetic.json

The own set (the default) is the user's judgments:
  review cases   in tests/feedback/cases.json, text the user rejected for a reason a regex cannot see: the
                 reviewer must flag each one with the case's criterion
  pass cases     in tests/feedback/cases.json, text the user approved: the reviewer must find nothing
  rewrite pairs  in tests/feedback/pairs.json (scripts/pairs.py): the agent's first version of a passage, which the
                 user sent back with feedback, and the agent's final version, which the user approved. The first
                 must be flagged (under the pair's criterion when it has one), the final must pass
and the user's published posts in social_samples (writing-rules.yaml, this repo's workspace/tone-of-voice/social/),
which must pass too: the post itself, without the voice library's header. A post that breaks a hard rule set after it
was posted is left out, with its reason, in tests/feedback/posts-left-out.json; the post stays in the voice library.

The reviewer counts as calibrated only when every review case and every first version is caught, no approved
text or published post is flagged, and the set is big enough to mean something (MIN_REVIEW_CASES and
MIN_PASS_CASES). Cases taken from the house rules' own examples (piece "house-rules") are run and must be caught,
but only the user's own corrections (review cases and rewrite pairs) count toward MIN_REVIEW_CASES. The record
holds the reviewer's fingerprint (model, effort, prompt, rubric and backend): change any of them and ai_review.py
reports itself uncalibrated until this runs again.

The synthetic set (tests/feedback/synthetic.json) is made-up text, one labelled pair per rubric criterion. It shows
whether the reviewer recognizes each criterion at all; it says nothing about the user's taste, so its record never
says calibrated and goes to its own file.

Each run costs money on the API backend, or usage of the user's Claude plan on the claude-cli backend
(REVIEWER_BACKEND, see ai_review.py).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_review  # noqa: E402
import doctor  # noqa: E402

ROOT = ai_review.ROOT
CASES = ROOT / "tests" / "feedback" / "cases.json"
PAIRS = ROOT / "tests" / "feedback" / "pairs.json"
SYNTHETIC = ROOT / "tests" / "feedback" / "synthetic.json"
SYNTHETIC_RECORD = ROOT / "tests" / "feedback" / "calibration-synthetic.json"
POSTS_LEFT_OUT = ROOT / "tests" / "feedback" / "posts-left-out.json"
MIN_REVIEW_CASES = 10  # below this, a perfect score says little about the next piece
MIN_PASS_CASES = 5
EXAMPLE_PIECE = "house-rules"  # cases taken from the rules' own examples, not from the user's corrections
# Rough per-call usage for the estimate: rubric and prompt plus a short case, and the reply with thinking.
EST_INPUT_TOKENS, EST_OUTPUT_TOKENS = 2500, 1500
PRICE_PER_MTOK = {"claude-opus-5-5": (4.00, 20.00)}  # input, output; check current pricing before relying on it


def load_pairs(path: Path = PAIRS) -> tuple[list[dict], list[dict]]:
    """Labelled rewrite pairs as (first versions to flag, final versions to pass). An unlabelled pair (calibrate null)
    and a pair labelled calibrate: false are left out; a cut passage (empty final) has nothing to pass."""
    if not path.exists():
        return [], []
    pairs = [p for p in json.loads(path.read_text(encoding="utf-8")).get("pairs", []) if p.get("calibrate") is True]
    firsts = [{"id": f"{p['id']}:first", "piece": p.get("piece"), "criterion": p.get("criterion"), "text": p["first"],
               "source": "pair"} for p in pairs]
    finals = [{"id": f"{p['id']}:final", "piece": p.get("piece"), "text": p["final"], "source": "pair"}
              for p in pairs if p["final"].strip()]
    return firsts, finals


def load_set(which: str = "own") -> tuple[list[dict], list[dict]]:
    if which == "synthetic":
        cases = json.loads(SYNTHETIC.read_text(encoding="utf-8"))["cases"]
        return [c for c in cases if c["expect"] == "review"], [c for c in cases if c["expect"] == "pass"]
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    negatives = [c for c in cases if c["expect"] == "review"]
    positives = [c for c in cases if c["expect"] == "pass"]
    firsts, finals = load_pairs()
    negatives += firsts
    positives += finals
    left_out = posts_left_out()
    positives += [{"id": f"post:{p.name}", "text": ai_review.sample_text(p.read_text(encoding="utf-8"))}
                  for p in published_posts() if p.name not in left_out]
    return negatives, positives


def published_posts() -> list[Path]:
    try:
        paths = doctor.resolve(doctor.parse_config(doctor.CONFIG.read_text(encoding="utf-8")))
        samples = Path(paths["social_samples"])
        return sorted(samples.glob("20*.md")) if samples.is_dir() else []
    except (KeyError, OSError):
        return []


def posts_left_out(path: Path = POSTS_LEFT_OUT) -> dict[str, str]:
    """{file name: why} for published posts that break a hard rule set after they were posted: the user's
    published words stay as they are in the voice library, and they stop being texts the reviewer must pass."""
    if not path.exists():
        return {}
    return {p["file"]: p["why"] for p in json.loads(path.read_text(encoding="utf-8")).get("posts", [])}


def judge(negatives: list[dict], positives: list[dict], run, which: str = "own", jobs: int = 1) -> dict:
    """Score the reviewer. run(text) returns ai_review.review()'s result. A negative with no criterion (a rewrite
    pair the user gave no criterion for) is caught by any finding."""
    def safe(text):
        try:
            return run(text)
        except Exception as exc:  # one failed review is reported; the rest of the run, already paid for, is kept
            return {"findings": [], "error": f"{type(exc).__name__}: {str(exc)[:200]}"}

    texts = [c["text"] for c in negatives + positives]
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        answers = list(pool.map(safe, texts))
    found_all = [a["findings"] for a in answers]
    errors = [a.get("error") for a in answers]
    results = []
    for case, found, error in zip(negatives, found_all[:len(negatives)], errors[:len(negatives)]):
        criteria = sorted({f["criterion"] for f in found})
        expected = case.get("criterion")
        if error:
            results.append({"id": case["id"], "expect": expected or "any finding", "got": [error], "outcome": "error"})
            continue
        if expected:
            outcome = "caught" if expected in criteria else ("wrong criterion" if found else "missed")
        else:
            outcome = "caught" if found else "missed"
        results.append({"id": case["id"], "expect": expected or "any finding", "got": criteria, "outcome": outcome})
    for case, found, error in zip(positives, found_all[len(negatives):], errors[len(negatives):]):
        if error:
            results.append({"id": case["id"], "expect": "nothing", "got": [error], "outcome": "error"})
            continue
        outcome = "passed" if not found else "false alarm"
        results.append({"id": case["id"], "expect": "nothing", "got": [f"{f['criterion']}: {f['quote'][:60]}" for f in found],
                        "outcome": outcome})
    caught = sum(r["outcome"] == "caught" for r in results)
    alarms = sum(r["outcome"] == "false alarm" for r in results)
    failed = sum(r["outcome"] == "error" for r in results)
    reasons = [f"{failed} review(s) failed to run"] if failed else []
    missed = len(negatives) - caught - sum(r["outcome"] == "error" for r in results[:len(negatives)])
    if missed:
        reasons.append(f"{missed} of {len(negatives)} rejected texts not caught with their criterion")
    if alarms:
        reasons.append(f"{alarms} approved text(s) flagged")
    if which == "synthetic":
        status = "smoke test passed" if not reasons else "smoke test failed"
        reasons.append("synthetic text: shows whether the reviewer knows each criterion, never a calibration on the user")
    else:
        own = [c for c in negatives if c.get("piece") != EXAMPLE_PIECE]
        if len(own) < MIN_REVIEW_CASES:
            reasons.append(f"only {len(own)} review cases from the user's corrections, {MIN_REVIEW_CASES} needed")
        if len(positives) < MIN_PASS_CASES:
            reasons.append(f"only {len(positives)} approved texts, {MIN_PASS_CASES} needed")
        status = "calibrated" if not reasons else "not calibrated"
    return {
        "status": status,
        "reason": "; ".join(reasons),
        "caught": f"{caught}/{len(negatives)}",
        "false_alarms": f"{alarms}/{len(positives)}",
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--set", dest="which", choices=("own", "synthetic"), default="own")
    ap.add_argument("--jobs", type=int, default=1, help="reviews to run at once (default 1)")
    args = ap.parse_args(argv)

    which_backend = ai_review.backend()
    negatives, positives = load_set(args.which)
    calls = len(negatives) + len(positives)
    price_in, price_out = PRICE_PER_MTOK.get(ai_review.MODEL, (0.0, 0.0))
    estimate = calls * (EST_INPUT_TOKENS * price_in + EST_OUTPUT_TOKENS * price_out) / 1_000_000
    cost = (f"about ${estimate:.2f} at API prices" if which_backend == "api"
            else f"on the Claude plan's usage (about ${estimate:.2f} at API prices)")
    print(f"{ai_review.MODEL}, effort {ai_review.EFFORT}, backend {which_backend}, "
          f"fingerprint {ai_review.fingerprint(backend_name=which_backend)}, set {args.which}")
    own = sum(c.get("piece") != EXAMPLE_PIECE for c in negatives)
    need = f" ({own} from the user's corrections, {MIN_REVIEW_CASES} needed)" if args.which == "own" else ""
    print(f"{len(negatives)} texts to flag{need}, {len(positives)} approved texts: {calls} calls, {cost}")
    if args.dry_run:
        for c in negatives:
            print(f"  must flag  {c['id']:34} as {c.get('criterion') or 'any finding'}")
        for c in positives:
            print(f"  must pass  {c['id']}")
        if args.which == "own":
            for name, why in posts_left_out().items():
                print(f"  left out  post:{name}: {why}")
        return 0

    client = ai_review.make_client(which_backend)
    usage = {"input_tokens": 0, "output_tokens": 0}
    lock = threading.Lock()

    def run(text: str) -> dict:
        result = ai_review.review(text, client=client)
        with lock:  # reviews finish on several threads at once with --jobs
            for k in usage:
                usage[k] += result["usage"][k]
        return result

    outcome = judge(negatives, positives, run, args.which, args.jobs)
    record = {
        "model": ai_review.MODEL, "effort": ai_review.EFFORT, "backend": which_backend, "set": args.which,
        "fingerprint": ai_review.fingerprint(backend_name=which_backend),
        "date": dt.date.today().isoformat(), **outcome, "usage": usage,
    }
    target = SYNTHETIC_RECORD if args.which == "synthetic" else ai_review.CALIBRATION
    target.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for r in outcome["results"]:
        print(f"  {r['outcome']:16} {r['id']:34} expected {r['expect']}, got {r['got'] or 'nothing'}")
    print(f"{outcome['status']}: caught {outcome['caught']}, false alarms {outcome['false_alarms']}"
          + (f" ({outcome['reason']})" if outcome["reason"] else ""))
    print(f"written to {target.relative_to(ROOT)}; commit it with the change that needed it")
    return 0 if outcome["status"] in ("calibrated", "smoke test passed") else 1


if __name__ == "__main__":
    sys.exit(main())
