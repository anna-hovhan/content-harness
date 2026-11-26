"""The AI-writing-pattern rules (house rules, section 2.2) are all evaluated, and nothing passes around them.

Every HR-ai- rule must say how it is evaluated (scripts/ai_patterns.py, COVERAGE): by the pattern scan, by an AI reviewer
criterion, by the commit-message check. This file fails when a rule has no evaluation, when an evaluation has no locked
example that still trips it, when the scoring table in the rubric drifts from the code, or when text the user approved
starts to fail. The locked examples live in tests/rules.lock (ai_pattern_samples, commit_message_samples).
Run: python3 -m unittest discover -s tests
"""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import ai_patterns  # noqa: E402
import ai_review  # noqa: E402
import test_check_text  # noqa: E402
import test_rule_sync  # noqa: E402

LOCK = json.loads((ROOT / "tests" / "rules.lock").read_text(encoding="utf-8"))
CASES = json.loads((ROOT / "tests" / "feedback" / "cases.json").read_text(encoding="utf-8"))["cases"]
RUBRIC = (ROOT / "system" / "00-core" / "test_review-rubric.md").read_text(encoding="utf-8")
HOUSE_RULES = (ROOT / "system" / "00-core" / "house-rules.md").read_text(encoding="utf-8")
SAMPLES = LOCK["ai_pattern_samples"]
AI_RULES = {rid for rid in test_rule_sync.house_rule_ids() if rid.startswith("HR-ai-")}


def hits_of(sample):
    return ai_patterns.scan(sample["text"], sample.get("channel"))


class CoverageTests(unittest.TestCase):
    def test_every_ai_rule_says_how_it_is_evaluated(self):
        self.assertEqual(AI_RULES, set(ai_patterns.COVERAGE),
                         "a rule in house-rules.md section 2.2 has no entry in ai_patterns.COVERAGE, or the reverse")
        for rule, kinds in ai_patterns.COVERAGE.items():
            self.assertTrue(kinds and set(kinds) <= {"scan", "reviewer", "commit"}, rule)

    def test_the_rules_sit_in_their_own_subsection(self):
        self.assertIn("### 2.1 Core style rules", HOUSE_RULES)
        self.assertIn("### 2.2 AI writing patterns", HOUSE_RULES)
        part = HOUSE_RULES.split("### 2.2 AI writing patterns", 1)[1].split("\n## 3.", 1)[0]
        self.assertEqual({r for r in test_rule_sync.ID.findall(part) if r.startswith("HR-ai-")}, AI_RULES)
        core = HOUSE_RULES.split("### 2.1 Core style rules", 1)[1].split("### 2.2", 1)[0]
        self.assertFalse([r for r in test_rule_sync.ID.findall(core) if r.startswith("HR-ai-")], "2.1 stays as it was")

    def test_every_scan_rule_has_a_locked_example_for_each_severity_it_uses(self):
        used = {(rule, sev) for rule, sev, _, _ in ai_patterns.PHRASE_CHECKS}
        locked = {(s["rule"], s["severity"]) for s in SAMPLES}
        self.assertFalse(used - locked, f"no locked example for {sorted(used - locked)}: add one to tests/rules.lock")
        for rule in (r for r, kinds in ai_patterns.COVERAGE.items() if "scan" in kinds):
            self.assertIn(rule, {s["rule"] for s in SAMPLES}, f"{rule} is evaluated by the scan but has no locked example")

    def test_every_locked_example_still_trips_its_rule(self):
        for sample in SAMPLES:
            with self.subTest(rule=sample["rule"], severity=sample["severity"]):
                hits = hits_of(sample)
                self.assertTrue(any(h["rule"] == sample["rule"] and h["severity"] == sample["severity"] for h in hits),
                                f"no longer a {sample['severity']} for {sample['rule']}: {sample['text'][:60]!r} -> {hits}")

    def test_errors_fail_check_text_and_warnings_do_not(self):
        for sample in SAMPLES:
            with self.subTest(rule=sample["rule"], severity=sample["severity"]):
                result = test_check_text.check(sample["text"], channel=sample.get("channel"))
                tagged = lambda items: any(sample["rule"] in item for item in items)  # noqa: E731
                if sample["severity"] == ai_patterns.HARD:
                    self.assertTrue(tagged(result["errors"]), result["errors"])
                else:
                    self.assertTrue(tagged(result["warnings"]), result["warnings"])
                    self.assertFalse(tagged(result["errors"]), "a warning must not be an error")

    def test_reviewer_rules_belong_to_a_rubric_criterion(self):
        criteria = ai_review.rubric_criteria()
        covered = {rule for rules in criteria.values() for rule in rules}
        for rule, kinds in ai_patterns.COVERAGE.items():
            if "reviewer" in kinds:
                self.assertIn(rule, covered, f"{rule} is evaluated by the reviewer but no rubric criterion lists it")

    def test_commit_message_rules_have_locked_examples(self):
        locked = LOCK["commit_message_samples"]
        for rule in (r for r, kinds in ai_patterns.COVERAGE.items() if "commit" in kinds):
            self.assertIn(rule, {c["rule"] for c in locked})
        for c in locked:
            with self.subTest(text=c["text"]):
                self.assertTrue(any(h["rule"] == c["rule"] for h in ai_patterns.commit_message_hits(c["text"])))
        self.assertEqual(ai_patterns.commit_message_hits("Cut the second paragraph's analogy and the closing question."), [])

    def test_every_new_review_case_names_a_criterion_and_is_locked(self):
        criteria = set(ai_review.rubric_criteria())
        for case in (c for c in CASES if c["id"].startswith("ai-") and c["expect"] == "review"):
            self.assertIn(case["criterion"], criteria)
        for case in (c for c in CASES if c["id"].startswith("ai-")):
            self.assertIn(case["id"], LOCK["feedback_cases"])


class NothingApprovedFailsTests(unittest.TestCase):
    def test_approved_text_has_no_hard_hit_and_passes_the_score(self):
        for case in (c for c in CASES if c["expect"] == "pass"):
            with self.subTest(case=case["id"]):
                result = ai_patterns.score(ai_patterns.scan(case["text"]))
                self.assertEqual(result["verdict"], "pass", result)

    def test_the_current_pieces_have_no_hard_hit(self):
        for path in (ROOT / "workspace" / "pieces").glob("*/article.md"):
            with self.subTest(piece=path.parent.name):
                result = ai_patterns.score(ai_patterns.scan(path.read_text(encoding="utf-8"), "LinkedIn article"))
                self.assertNotEqual(result["verdict"], "fail", result)


class ScanScopeTests(unittest.TestCase):
    def test_code_comments_and_scaffold_sections_are_not_read(self):
        text = ("# Title\n\nA plain sentence.\n\n```\nIt plays a pivotal role.\n```\n\nUse `serves as` sparingly.\n\n"
                "<!-- I hope this helps! -->\n\n## Check before posting\n\n- Check this before publishing.\n")
        self.assertEqual(ai_patterns.scan(text), [])

    def test_markdown_is_only_an_error_in_a_post(self):
        text = "## Post\n\nA **bold** claim with [a link](https://example.org).\n"
        self.assertFalse([h for h in ai_patterns.scan(text, "LinkedIn article") if h["rule"] == "HR-ai-channel-markup"])
        self.assertEqual({h["rule"] for h in ai_patterns.scan(text, "LinkedIn post")}, {"HR-ai-channel-markup"})

    def test_a_post_draft_is_checked_in_its_post_section_only(self):
        text = "# LinkedIn post: x\n\n## Post\n\nPlain text.\n\n## Other hooks to try\n\n1. A **bold** hook.\n"
        self.assertEqual(ai_patterns.scan(text, "LinkedIn post"), [])

    def test_one_phrase_is_counted_once(self):
        hits = ai_patterns.scan("It plays a pivotal role.")
        self.assertEqual(len(hits), 1, hits)


class ScoringTests(unittest.TestCase):
    def test_the_rubric_table_matches_the_code(self):
        table = re.findall(r"^\|\s*(Error|Warning)[^|]*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", RUBRIC, re.M)
        rows = {name: tuple(int(x) for x in rest) for name, *rest in table}
        self.assertEqual(rows["Error"], ai_patterns.WEIGHTS[ai_patterns.HARD])
        self.assertEqual(rows["Warning"], ai_patterns.WEIGHTS[ai_patterns.SOFT])
        self.assertRegex(RUBRIC, rf"\|\s*Reviewer finding\s*\|\s*{ai_patterns.FINDING_COST}\s*\|")
        self.assertIn(f"pass from {ai_patterns.PASS_FROM}", RUBRIC)
        self.assertIn(f"fail below {ai_patterns.FAIL_BELOW}", RUBRIC)

    def test_points_are_lost_per_rule_with_a_cap(self):
        soft = {"rule": "HR-ai-straight-quotes", "severity": "warning", "line": 1, "message": ""}
        self.assertEqual(ai_patterns.score([soft])["score"], 96)
        self.assertEqual(ai_patterns.score([soft] * 2)["score"], 94)
        self.assertEqual(ai_patterns.score([soft] * 50)["score"], 100 - ai_patterns.WEIGHTS["warning"][2])

    def test_an_error_fails_whatever_the_score(self):
        hard = {"rule": "HR-ai-no-chat-residue", "severity": "error", "line": 1, "message": ""}
        self.assertEqual(ai_patterns.score([hard])["verdict"], "fail")
        self.assertGreaterEqual(ai_patterns.score([hard])["score"], ai_patterns.FAIL_BELOW)

    def test_reviewer_findings_cost_points(self):
        out = ai_patterns.score([], [{"criterion": "generic-claim"}, {"criterion": "chat-residue"}])
        self.assertEqual(out["score"], 100 - 2 * ai_patterns.FINDING_COST)
        self.assertEqual(out["verdict"], "review")

    def test_many_soft_signs_fail_the_check_without_a_single_error(self):
        soft = [s["text"] for s in SAMPLES if s["severity"] == "warning" and not s.get("channel")
                and s["rule"] not in ("HR-ai-varied-rhythm", "HR-ai-no-abrupt-end", "HR-ai-heading-levels", "HR-ai-prose-default")]
        text = "\n\n".join(soft)
        result = test_check_text.check(text)
        self.assertTrue(any(e.startswith("AI-pattern score") for e in result["errors"]), result["score"])
        self.assertEqual([e for e in result["errors"] if not e.startswith("AI-pattern score")], [], "only the score fails here")


class OrdinaryProseTests(unittest.TestCase):
    """The checks set on 2026-11-24 catch the wording the user ruled out and leave ordinary sentences alone."""

    def hits(self, text, rule):
        return [h["severity"] for h in ai_patterns.scan(text) if h["rule"] == rule]

    def test_hold_for_works_or_applies_is_an_error(self):
        for text in ("A rule holds when the agent cannot edit its check.", "Whether it holds depends on the harness.",
                     "Whether it holds is up to the harness.", "It holds up in production.", "That still holds true.",
                     "The rules hold for every channel.", "The idea holds when the data is clean.", "The formula holds true.",
                     "The agenda holds until Friday.", "The rule holds.", "The claim does not hold.",
                     "The assumption no longer holds.", "The rule held up for a month.", "The rule held for a month.",
                     "The rules held when I tested them.", "The rule is holding up in production."):
            with self.subTest(text=text):
                self.assertIn(ai_patterns.HARD, self.hits(text, "HR-ai-no-holds"))

    def test_hold_with_an_object_as_a_noun_or_as_a_command_is_no_error(self):
        for text in ("This file holds the final text.", "The lock holds 68 house rules.", "It holds only what the user has said.",
                     "The role is on hold for now.", "CI tests hold the brand rules against the templates.",
                     "The output is held to a JSON schema.", "The knowledge only one or two people hold.",
                     "A missing answer does not hold up the draft.", "A claim the user holds because of what happened.",
                     "The review was held up by a missing answer.", "I got held up at work.", "The traffic held up the delivery.",
                     "Delays hold up reviews.", "A missing answer holds up delivery.", "Press and hold for two seconds.",
                     "Hold until the pull request is merged.", "The legal hold for the files ends in May.",
                     "This file holds for each channel a list of sizes.", "The cache holds, under each key, a list.",
                     "Check whether it holds data."):
            with self.subTest(text=text):
                self.assertNotIn(ai_patterns.HARD, self.hits(text, "HR-ai-no-holds"))

    def test_lives_and_sits_warn_for_things_and_pass_for_people(self):
        for text in ("The rules live in one file.", "The check sits in CI.", "The repo sits upstream of the others."):
            with self.subTest(text=text):
                self.assertEqual(self.hits(text, "HR-ai-no-holds"), [ai_patterns.SOFT])
        for text in ("I live in Amsterdam.", "She sat on the hiring panel.", "My parents live in Lisbon.",
                     "People that live in Lisbon.", "Engineers that sit in the platform team."):
            with self.subTest(text=text):
                self.assertEqual(self.hits(text, "HR-ai-no-holds"), [])

    def test_three_items_with_one_possessive_fail(self):
        for text in ("My writing, my notes, my images, and my portfolio site.", "Our goals, our plans, our numbers.",
                     "Bring your team, your tools and your data.", "My writing; my notes; my images."):
            with self.subTest(text=text):
                self.assertEqual(self.hits(text, "HR-ai-no-repeated-list-opener"), [ai_patterns.HARD])

    def test_two_items_mixed_openers_and_clauses_pass(self):
        for text in ("Send my name and my email.", "A private term: my name, an employer, a company I applied to.",
                     "A content harness, a design assistant, a notes app and my site.",
                     "I told my manager, my manager told her team, and my team heard it last.",
                     "She gave her notes, her manager gave her feedback, and her team shipped."):
            with self.subTest(text=text):
                self.assertEqual(self.hits(text, "HR-ai-no-repeated-list-opener"), [])


class CommandLineTests(unittest.TestCase):
    def run_cli(self, text, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "test_check_text.py"), "-", *args], input=text,
                              capture_output=True, text=True)

    def test_standard_input_is_checked(self):
        bad = self.run_cli("It plays a pivotal role.\n")
        self.assertEqual(bad.returncode, 1)
        self.assertIn("HR-ai-no-significance-claims", bad.stdout)
        self.assertEqual(self.run_cli("The vault keeps notes in a folder.\n").returncode, 0)

    def test_the_channel_option_reaches_the_post_check(self):
        self.assertEqual(self.run_cli("A **bold** post.\n", "--channel", "LinkedIn post").returncode, 1)
        self.assertEqual(self.run_cli("A **bold** post.\n").returncode, 0)


if __name__ == "__main__":
    unittest.main()
