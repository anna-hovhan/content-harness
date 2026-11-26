"""Offline tests for the AI reviewer: no API call, no anthropic package needed.

They hold the reviewer to its rubric and its calibration set: every criterion enforces real house rules,
every review case names a criterion the rubric has, the request is pinned, findings without a real quote
are dropped, and a calibration record that no longer matches the model, prompt or rubric fails the build.
Run: python3 -m unittest discover -s tests
"""
import json
import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import ai_review  # noqa: E402
import test_calibrate_reviewer  # noqa: E402
import test_check_text  # noqa: E402
import test_rule_sync  # noqa: E402

CASES = json.loads((ROOT / "tests" / "feedback" / "cases.json").read_text(encoding="utf-8"))["cases"]
LOCK = json.loads((ROOT / "tests" / "rules.lock").read_text(encoding="utf-8"))


class FakeClient:
    """Answers every review with the findings it was given."""
    def __init__(self, findings):
        self.findings, self.requests = findings, []
        self.messages = self

    def create(self, **kwargs):
        self.requests.append(kwargs)
        text = json.dumps({"findings": self.findings(kwargs) if callable(self.findings) else self.findings})
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=text)],
                               usage=SimpleNamespace(input_tokens=10, output_tokens=5))


class RubricTests(unittest.TestCase):
    def test_every_criterion_enforces_existing_house_rules(self):
        known = test_rule_sync.house_rule_ids()
        for criterion, rules in ai_review.rubric_criteria().items():
            with self.subTest(criterion=criterion):
                self.assertTrue(rules, "a criterion names the house rules it enforces")
                self.assertFalse(set(rules) - set(known), f"unknown rule IDs {set(rules) - set(known)}")

    def test_criteria_match_the_lock(self):
        current, locked = set(ai_review.rubric_criteria()), set(LOCK["review_criteria"])
        self.assertFalse(locked - current, f"rubric criteria removed: {sorted(locked - current)}. "
                         "Change tests/rules.lock in the same commit, with the user's yes.")
        self.assertFalse(current - locked, f"new rubric criteria not in the lock yet: {sorted(current - locked)}")

    def test_what_the_rubric_says_the_script_catches_it_catches(self):
        text = ai_review.RUBRIC.read_text(encoding="utf-8")
        section = text.split("## Caught by test_check_text.py", 1)[1].split("\n## ", 1)[0]
        examples = [e for line in section.splitlines() if line.startswith("- ") for e in re.findall(r"`([^`]+)`", line)]
        self.assertTrue(examples, "the rubric lists what test_check_text.py catches")
        for example in examples:
            with self.subTest(example=example):
                self.assertTrue(test_check_text.check(example)["errors"],
                                "the rubric says test_check_text.py catches this, but it passes: move it under a criterion's 'Script misses'")

    def test_what_the_rubric_says_the_script_misses_it_misses(self):
        lines = [l for l in ai_review.RUBRIC.read_text(encoding="utf-8").splitlines() if l.startswith("Script misses:")]
        examples = [e for line in lines for e in re.findall(r"`([^`]+)`", line)]
        self.assertTrue(examples, "the criteria list the forms test_check_text.py misses")
        for example in examples:
            with self.subTest(example=example):
                self.assertEqual(test_check_text.check(example)["errors"], [],
                                 "test_check_text.py now catches this: move it under 'Caught by test_check_text.py'")

    def test_every_review_case_names_a_rubric_criterion(self):
        criteria = set(ai_review.rubric_criteria())
        for case in (c for c in CASES if c["expect"] == "review"):
            with self.subTest(case=case["id"]):
                self.assertIn(case.get("criterion"), criteria)


class ReviewerTests(unittest.TestCase):
    def test_request_is_pinned_and_structured(self):
        req = ai_review.build_request("A draft.")
        self.assertEqual(req["model"], ai_review.MODEL)
        self.assertEqual(req["output_config"]["effort"], ai_review.EFFORT)
        schema = req["output_config"]["format"]["schema"]
        enum = schema["properties"]["findings"]["items"]["properties"]["criterion"]["enum"]
        self.assertEqual(enum, list(ai_review.rubric_criteria()))
        self.assertNotIn("temperature", req)
        self.assertIn("<draft>\nA draft.\n</draft>", req["messages"][0]["content"][-1]["text"])

    def test_findings_need_a_quote_from_the_text(self):
        text = "Think of Claude as a very diligent chief of staff."
        client = FakeClient([
            {"criterion": "explaining-down", "quote": "a very diligent chief of staff", "why": "analogy"},
            {"criterion": "selling", "quote": "saves hours every week", "why": "invented"},
        ])
        result = ai_review.review(text, client=client)
        self.assertEqual([f["criterion"] for f in result["findings"]], ["explaining-down"])
        self.assertEqual(len(result["dropped"]), 1)

    def test_quotes_match_across_curly_quotes_and_markdown(self):
        kept = ai_review.parse_findings(json.dumps({"findings": [{"criterion": "selling", "quote": "Try it, break it", "why": "x"}]}),
                                        "## **Try it, break it**, tell me what’s missing")
        self.assertEqual(len(kept["findings"]), 1)

    def test_a_refusal_is_an_error_not_a_pass(self):
        with self.assertRaises(RuntimeError):
            ai_review.response_text(SimpleNamespace(stop_reason="refusal", content=[]))

    def test_the_fingerprint_follows_model_and_rubric(self):
        base = ai_review.fingerprint("rubric")
        self.assertNotEqual(base, ai_review.fingerprint("rubric, edited"))
        model = ai_review.MODEL
        try:
            ai_review.MODEL = "another-model"
            self.assertNotEqual(base, ai_review.fingerprint("rubric"))
        finally:
            ai_review.MODEL = model


class CalibrationTests(unittest.TestCase):
    def test_judge_scores_catches_misses_and_false_alarms(self):
        negatives = [{"id": "n1", "text": "flag me", "criterion": "selling"},
                     {"id": "n2", "text": "miss me", "criterion": "obvious"}]
        positives = [{"id": "p1", "text": "fine"}, {"id": "p2", "text": "alarm"}]

        def run(text):
            found = {"flag me": [{"criterion": "selling", "quote": "flag me"}],
                     "alarm": [{"criterion": "flourish", "quote": "alarm"}]}.get(text, [])
            return {"findings": found}

        out = test_calibrate_reviewer.judge(negatives, positives, run)
        self.assertEqual([r["outcome"] for r in out["results"]], ["caught", "missed", "passed", "false alarm"])
        self.assertEqual(out["status"], "not calibrated")

    def test_a_perfect_score_on_a_small_set_is_not_calibration(self):
        negatives = [{"id": "n", "text": "x", "criterion": "selling"}]
        out = test_calibrate_reviewer.judge(negatives, [], lambda t: {"findings": [{"criterion": "selling", "quote": "x"}]})
        self.assertIn("review cases", out["reason"])
        self.assertEqual(out["status"], "not calibrated")

    def test_house_rules_examples_do_not_count_toward_the_minimum(self):
        negatives = [{"id": f"n{i}", "text": "x", "criterion": "selling", "piece": "house-rules"} for i in range(12)]
        positives = [{"id": f"p{i}", "text": "y"} for i in range(5)]
        run = lambda t: {"findings": [{"criterion": "selling", "quote": "x"}] if t == "x" else []}  # noqa: E731
        out = test_calibrate_reviewer.judge(negatives, positives, run)
        self.assertEqual(out["status"], "not calibrated")
        self.assertIn("0 review cases from the user's corrections", out["reason"])

    def test_the_committed_calibration_matches_the_reviewer(self):
        if not ai_review.CALIBRATION.exists():
            self.skipTest("no calibration run yet")
        record = json.loads(ai_review.CALIBRATION.read_text(encoding="utf-8"))
        self.assertEqual(record["fingerprint"], ai_review.fingerprint(backend_name=record.get("backend", "api")),
                         f"the model, prompt or rubric changed after the calibration of {record['date']}: "
                         "rerun python3 scripts/test_calibrate_reviewer.py and commit tests/feedback/calibration.json")


class BackendTests(unittest.TestCase):
    """The claude-cli backend sends the same request as the API and is a reviewer of its own."""

    def test_the_cli_command_carries_the_pinned_request_and_no_tools(self):
        req = ai_review.build_request("A draft.")
        cmd = ai_review.ClaudeCliClient.command(req, "claude")
        self.assertEqual(cmd[cmd.index("--model") + 1], ai_review.MODEL)
        self.assertEqual(cmd[cmd.index("--effort") + 1], ai_review.EFFORT)
        self.assertEqual(cmd[cmd.index("--system-prompt") + 1], ai_review.SYSTEM_PROMPT)
        self.assertEqual(json.loads(cmd[cmd.index("--json-schema") + 1]), req["output_config"]["format"]["schema"])
        self.assertEqual(cmd[cmd.index("--tools") + 1], "")
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "")
        for flag in ("--no-session-persistence", "--strict-mcp-config"):
            self.assertIn(flag, cmd)
        self.assertIn("<draft>\nA draft.\n</draft>", ai_review.ClaudeCliClient.prompt(req))

    def test_the_cli_answer_reads_like_the_sdk_response(self):
        out = json.dumps({"subtype": "success", "is_error": False, "stop_reason": "tool_use",
                          "structured_output": {"findings": [{"criterion": "selling", "quote": "Try it", "why": "x"}]},
                          "usage": {"input_tokens": 2, "cache_creation_input_tokens": 600, "output_tokens": 50}})
        calls = []

        def runner(cmd, **kw):
            calls.append((cmd, kw))
            return SimpleNamespace(returncode=0, stdout=out, stderr="")

        result = ai_review.review("Try it today.", client=ai_review.ClaudeCliClient("claude", runner=runner))
        self.assertEqual([f["criterion"] for f in result["findings"]], ["selling"])
        self.assertEqual(result["usage"], {"input_tokens": 602, "output_tokens": 50})
        self.assertNotEqual(Path(calls[0][1]["cwd"]).resolve(), ROOT.resolve(), "the CLI must run outside the repo")

    def test_a_failed_cli_run_is_an_error_not_a_pass(self):
        bad = json.dumps({"subtype": "error_max_turns", "is_error": True, "result": "stopped"})
        with self.assertRaises(RuntimeError):
            ai_review.ClaudeCliClient.parse(bad)
        runner = lambda cmd, **kw: SimpleNamespace(returncode=1, stdout="", stderr="not logged in")  # noqa: E731
        with self.assertRaises(RuntimeError):
            ai_review.review("x", client=ai_review.ClaudeCliClient("claude", runner=runner))

    def test_the_backend_is_part_of_the_fingerprint_but_the_api_fingerprint_is_unchanged(self):
        self.assertNotEqual(ai_review.fingerprint("r"), ai_review.fingerprint("r", backend_name="claude-cli"))
        self.assertEqual(ai_review.fingerprint("r"), ai_review.fingerprint("r", backend_name="api"))

    def test_an_unknown_backend_is_refused(self):
        import os
        old = os.environ.get("REVIEWER_BACKEND")
        os.environ["REVIEWER_BACKEND"] = "gpt"
        try:
            with self.assertRaises(SystemExit):
                ai_review.backend()
        finally:
            if old is None:
                os.environ.pop("REVIEWER_BACKEND")
            else:
                os.environ["REVIEWER_BACKEND"] = old


class SyntheticSetTests(unittest.TestCase):
    """The smoke-test set: made-up pairs, one per criterion, that the reviewer and only the reviewer can catch."""
    DOC = json.loads((ROOT / "tests" / "feedback" / "synthetic.json").read_text(encoding="utf-8"))

    def test_one_pair_per_criterion_except_the_voice(self):
        criteria = set(ai_review.rubric_criteria()) - {"not-the-voice"}
        rejected = {c["criterion"] for c in self.DOC["cases"] if c["expect"] == "review"}
        self.assertEqual(rejected, criteria)
        pairs = {}
        for c in self.DOC["cases"]:
            pairs.setdefault(c["pair"], []).append(c["expect"])
        self.assertTrue(all(sorted(v) == ["pass", "review"] for v in pairs.values()), pairs)

    def test_every_synthetic_text_is_out_of_the_scripts_reach(self):
        for c in self.DOC["cases"]:
            with self.subTest(case=c["id"]):
                self.assertEqual(test_check_text.check(c["text"])["errors"], [],
                                 "a fault the script catches is not a test of the reviewer")

    def test_synthetic_text_never_counts_as_calibration(self):
        neg, pos = test_calibrate_reviewer.load_set("synthetic")
        everything = lambda t: {"findings": [{"criterion": c["criterion"], "quote": "x"} for c in neg if c["text"] == t]}  # noqa: E731
        out = test_calibrate_reviewer.judge(neg, pos, everything, "synthetic")
        self.assertEqual(out["status"], "smoke test passed")
        self.assertNotIn(out["status"], ("calibrated",))
        self.assertFalse(any(c["id"].startswith("syn-") for c in CASES), "synthetic cases stay out of cases.json")


class PairCalibrationTests(unittest.TestCase):
    def test_labelled_pairs_join_the_own_set_and_unlabelled_ones_wait(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pairs.json"
            path.write_text(json.dumps({"pairs": [
                {"id": "p-1", "piece": "x", "first": "a", "final": "b", "criterion": "selling", "calibrate": True},
                {"id": "p-2", "piece": "x", "first": "c", "final": "", "criterion": None, "calibrate": True},
                {"id": "p-3", "piece": "x", "first": "e", "final": "f", "criterion": None, "calibrate": None},
                {"id": "p-4", "piece": "x", "first": "g", "final": "h", "criterion": None, "calibrate": False}]}))
            firsts, finals = test_calibrate_reviewer.load_pairs(path)
        self.assertEqual([f["id"] for f in firsts], ["p-1:first", "p-2:first"])
        self.assertEqual([f["id"] for f in finals], ["p-1:final"], "a cut passage has no final to pass")

    def test_a_pair_without_a_criterion_is_caught_by_any_finding(self):
        neg = [{"id": "p:first", "text": "t", "criterion": None, "piece": "x"}]
        out = test_calibrate_reviewer.judge(neg, [], lambda t: {"findings": [{"criterion": "obvious", "quote": "t"}]})
        self.assertEqual(out["results"][0]["outcome"], "caught")
        out = test_calibrate_reviewer.judge(neg, [], lambda t: {"findings": []})
        self.assertEqual(out["results"][0]["outcome"], "missed")


class ReviewFixTests(unittest.TestCase):
    def test_one_failed_review_is_an_error_and_the_rest_is_kept(self):
        neg = [{"id": "n1", "text": "boom", "criterion": "selling"}, {"id": "n2", "text": "flag", "criterion": "selling"}]
        pos = [{"id": "p1", "text": "fine"}]

        def run(text):
            if text == "boom":
                raise RuntimeError("claude -p timed out")
            return {"findings": [{"criterion": "selling", "quote": "flag"}] if text == "flag" else []}

        out = test_calibrate_reviewer.judge(neg, pos, run, jobs=2)
        self.assertEqual([r["outcome"] for r in out["results"]], ["error", "caught", "passed"])
        self.assertEqual(out["status"], "not calibrated")
        self.assertIn("1 review(s) failed to run", out["reason"])

    def test_a_calibration_on_another_backend_says_so(self):
        import tempfile
        old = ai_review.CALIBRATION
        with tempfile.TemporaryDirectory() as tmp:
            ai_review.CALIBRATION = Path(tmp) / "calibration.json"
            ai_review.CALIBRATION.write_text(json.dumps({"backend": "claude-cli", "date": "2026-11-25",
                                                         "fingerprint": "x", "status": "calibrated"}))
            try:
                status = ai_review.calibration_status("api")
            finally:
                ai_review.CALIBRATION = old
        self.assertIn("not calibrated for the api backend", status)
        self.assertNotIn("model, prompt or rubric changed", status)

class PublishedPostTests(unittest.TestCase):
    def test_the_reviewer_reads_the_post_not_the_samples_header(self):
        sample = ('# Sample: a post\n# Posted: 2026-11-19\n# Image: the card "From personal AI to company AI"\n'
                  '# Words: 9\n\nA team draws on two kinds of context.\n\nThe second paragraph.')
        self.assertEqual(ai_review.sample_text(sample), "A team draws on two kinds of context.\n\nThe second paragraph.")
        self.assertEqual(ai_review.sample_text("No header here."), "No header here.")

    def test_posts_left_out_name_real_posts_and_real_hard_rules(self):
        doc = json.loads((ROOT / "tests" / "feedback" / "posts-left-out.json").read_text(encoding="utf-8"))
        house = (ROOT / "system" / "00-core" / "house-rules.md").read_text(encoding="utf-8")
        hard = house.split("## 3.")[0]  # sections 1 and 2 are the hard rules
        posts = {p.name for p in test_calibrate_reviewer.published_posts()}
        for entry in doc["posts"]:
            with self.subTest(post=entry["file"]):
                self.assertIn(f"`{entry['rule']}`", hard, "a post is left out only for a hard rule")
                if posts:
                    self.assertIn(entry["file"], posts)
                self.assertTrue(entry["why"])

    def test_a_left_out_post_is_not_a_must_pass_text(self):
        _, positives = test_calibrate_reviewer.load_set("own")
        ids = {c["id"] for c in positives}
        for name in test_calibrate_reviewer.posts_left_out():
            self.assertNotIn(f"post:{name}", ids)
        for c in positives:
            if c["id"].startswith("post:"):
                self.assertFalse(c["text"].startswith("# Sample:"), "the header is not part of the post")

class HeaderVariantTests(unittest.TestCase):
    def test_any_header_key_and_a_blank_line_inside_the_header_are_stripped(self):
        sample = "# Sample: x\n# Cross-posted: y\n\n# URL2: z\n\nThe post."
        self.assertEqual(ai_review.sample_text(sample), "The post.")

if __name__ == "__main__":
    unittest.main()
