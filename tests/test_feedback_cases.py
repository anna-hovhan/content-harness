"""The user's corrections as tests: what they rejected must fail, what they approved must pass.

Cases live in tests/feedback/cases.json; the human-readable record is workspace/feedback-log.md.
Run: python3 -m unittest discover -s tests
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import test_check_text  # noqa: E402
import doctor  # noqa: E402

CASES = json.loads((ROOT / "tests" / "feedback" / "cases.json").read_text(encoding="utf-8"))["cases"]
LOCKED = set(json.loads((ROOT / "tests" / "rules.lock").read_text(encoding="utf-8"))["feedback_cases"])
EXPECT = {"error", "pass", "review"}
# The checks most likely to misfire on real prose; the user's own posts must never trip them.
STRUCTURAL = ("montage", "staccato", "starts with 'I' or 'We'")


class FeedbackCaseTests(unittest.TestCase):
    def test_cases_are_well_formed(self):
        ids = [c["id"] for c in CASES]
        self.assertEqual(len(ids), len(set(ids)), "duplicate case ids")
        for c in CASES:
            with self.subTest(case=c.get("id")):
                self.assertIn(c["expect"], EXPECT)
                for field in ("id", "date", "piece", "feedback", "text"):
                    self.assertTrue(c.get(field), f"missing {field}")
                if c["expect"] == "error":
                    self.assertTrue(c.get("contains"), "an error case names the message it expects")

    def test_every_case_is_locked(self):
        new = {c["id"] for c in CASES} - LOCKED
        self.assertFalse(new, f"add these case ids to tests/rules.lock: {sorted(new)}")

    def test_rejected_text_fails_the_checker(self):
        for c in (c for c in CASES if c["expect"] == "error"):
            with self.subTest(case=c["id"]):
                errors = test_check_text.check(c["text"])["errors"]
                self.assertTrue(any(c["contains"] in e for e in errors),
                                f"the checker no longer catches '{c['id']}' ({c['feedback']}): {errors}")

    def test_approved_text_passes_the_checker(self):
        for c in (c for c in CASES if c["expect"] == "pass"):
            with self.subTest(case=c["id"]):
                self.assertEqual(test_check_text.check(c["text"])["errors"], [], f"approved text '{c['id']}' now fails")

    def test_own_posts_pass_the_structural_checks(self):
        """Reads the user's published posts from social_samples (writing-rules.yaml), which this repo keeps, so CI runs it too."""
        samples = Path(doctor.resolve(doctor.parse_config(doctor.CONFIG.read_text(encoding="utf-8")))["social_samples"])
        posts = sorted(p for p in samples.glob("20*.md")) if samples.is_dir() else []
        if not posts:
            self.skipTest(f"no published posts in {samples}")
        for post in posts:
            with self.subTest(post=post.name):
                errors = test_check_text.check(post.read_text(encoding="utf-8"))["errors"]
                hits = [e for e in errors if any(s in e for s in STRUCTURAL)]
                self.assertEqual(hits, [], f"a check misfires on the user's own post {post.name}")


if __name__ == "__main__":
    unittest.main()
