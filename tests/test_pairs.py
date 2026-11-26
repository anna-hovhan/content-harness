"""Offline tests for scripts/pairs.py and the Stop hook that runs it: the agent's first version of a piece is saved
once, when the user is about to read it; when the user approves the piece, every passage the agent rewrote or cut
becomes an unlabelled rewrite pair; labels follow the rubric. A throwaway repo layout, nothing real touched.
Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import pairs  # noqa: E402
import test_check_content  # noqa: E402

HEADER = "| Date | Piece | Channel | Status | Folder | Published at |\n|---|---|---|---|---|---|\n"
FIRST = ("# Agents need owners\n\nThe triage agent is like a very diligent receptionist who never sleeps.\n\n"
         "It reads each ticket with one LLM call.\n\n[IMAGE v1: cover]\n\nAI can make mistakes, so check it.\n")
FINAL = ("# Agents need owners\n\nThe triage agent tags each ticket with a product and an urgency.\n\n"
         "It reads each ticket with one LLM call.\n\n[IMAGE v1: cover]\n")


def make_repo(status: str):
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    piece = root / "workspace" / "pieces" / "2026-11-25-agents"
    piece.mkdir(parents=True)
    set_status(root, status)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    return tmp, root, piece


def set_status(root: Path, status: str) -> None:
    (root / "workspace" / "content-log.md").write_text(
        HEADER + f"| 2026-11-25 | Agents | LinkedIn article | {status} | `pieces/2026-11-25-agents/` | not yet |\n",
        encoding="utf-8")


class RewriteTests(unittest.TestCase):
    def test_rewritten_and_cut_passages_pair_and_unchanged_ones_do_not(self):
        got = pairs.rewrites(FIRST, FINAL)
        self.assertEqual(got, [
            ("The triage agent is like a very diligent receptionist who never sleeps.",
             "The triage agent tags each ticket with a product and an urgency."),
            ("AI can make mistakes, so check it.", ""),
        ])

    def test_whitespace_alone_is_not_a_rewrite(self):
        self.assertEqual(pairs.rewrites("One line.\n\nTwo  lines.", "One line.\n\nTwo lines.\n"), [])

    def test_image_markers_and_code_are_not_passages(self):
        self.assertEqual(pairs.passages("A.\n\n[IMAGE v2: x]\n\n```\ncode\n```\n\nB."), ["A.", "B."])


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp, self.root, self.piece = make_repo("review")
        self.addCleanup(self.tmp.cleanup)

    def test_first_version_is_saved_once_at_review_and_paired_at_approval(self):
        (self.piece / "draft.md").write_text(FIRST, encoding="utf-8")
        self.assertEqual(pairs.snapshot_ready(self.root), ["2026-11-25-agents"])
        (self.piece / "draft.md").write_text(FINAL, encoding="utf-8")
        self.assertEqual(pairs.snapshot_ready(self.root), [], "the first version is never overwritten")
        pairs.add_feedback(self.piece, "No analogies for an agent. Cut the obvious line.", today="2026-11-25")
        self.assertEqual(pairs.capture_ready(self.root), {}, "nothing is captured before the user approves")
        set_status(self.root, "final")
        self.assertEqual(pairs.capture_ready(self.root), {"2026-11-25-agents": 2})
        doc = pairs.load(self.root)
        self.assertEqual([p["id"] for p in doc["pairs"]], ["2026-11-25-agents-1", "2026-11-25-agents-2"])
        self.assertIn("No analogies", doc["pairs"][0]["feedback"])
        self.assertTrue(all(p["calibrate"] is None for p in doc["pairs"]), "new pairs wait for a label")
        self.assertEqual(pairs.capture_ready(self.root), {}, "a piece is captured once")

    def test_the_approved_copy_wins_over_the_draft(self):
        (self.piece / "draft.md").write_text(FIRST, encoding="utf-8")
        pairs.snapshot_ready(self.root)
        (self.piece / "article.md").write_text(FINAL, encoding="utf-8")
        set_status(self.root, "posted")
        pairs.capture_ready(self.root)
        self.assertEqual(pairs.load(self.root)["pairs"][0]["file"], "draft.md -> article.md")

    def test_a_snapshot_waits_until_the_copy_passes_the_checks(self):
        (self.piece / "draft.md").write_text(FIRST, encoding="utf-8")
        self.assertEqual(pairs.snapshot_ready(self.root, is_clean=lambda f: False), [])
        self.assertEqual(pairs.snapshot_ready(self.root, is_clean=lambda f: True), ["2026-11-25-agents"])

    def test_labels_follow_the_rubric(self):
        (self.piece / "draft.md").write_text(FIRST, encoding="utf-8")
        pairs.snapshot_ready(self.root)
        (self.piece / "draft.md").write_text(FINAL, encoding="utf-8")
        set_status(self.root, "final")
        pairs.capture_ready(self.root)
        p = pairs.label("2026-11-25-agents-1", criterion="explaining-down", root=self.root)
        self.assertEqual((p["criterion"], p["calibrate"]), ("explaining-down", True))
        with self.assertRaises(SystemExit):
            pairs.label("2026-11-25-agents-2", criterion="not-a-criterion", root=self.root)
        p = pairs.label("2026-11-25-agents-2", skip="a fact the user corrected", root=self.root)
        self.assertEqual((p["calibrate"], p["label_note"]), (False, "a fact the user corrected"))
        self.assertEqual(pairs.unlabelled(self.root), [])


class StopHookTests(unittest.TestCase):
    def setUp(self):
        self.tmp, self.root, self.piece = make_repo("review")
        self.addCleanup(self.tmp.cleanup)

    def test_the_stop_hook_snapshots_captures_and_asks_for_labels(self):
        clean_first = "# Agents need owners\n\nThe agent reads each ticket.\n\nIt tags a product.\n"
        (self.piece / "draft.md").write_text(clean_first, encoding="utf-8")
        test_check_content.decide_stop({}, self.root)
        self.assertTrue((self.piece / pairs.FIRST_DIR / "meta.json").exists())
        (self.piece / "draft.md").write_text("# Agents need owners\n\nThe agent reads each ticket.\n\nIt tags a "
                                             "product and an urgency.\n", encoding="utf-8")
        set_status(self.root, "final")
        out = test_check_content.decide_stop({}, self.root)
        self.assertEqual(out["decision"], "block")
        self.assertIn("pairs.py label", out["reason"])
        self.assertEqual(len(pairs.load(self.root)["pairs"]), 1)

    def test_pairs_are_kept_even_on_the_turn_the_hook_already_blocked(self):
        (self.piece / "draft.md").write_text("# T\n\nThe agent reads each ticket.\n", encoding="utf-8")
        self.assertIsNone(test_check_content.decide_stop({"stop_hook_active": True}, self.root))
        self.assertTrue((self.piece / pairs.FIRST_DIR / "meta.json").exists())

    def test_snapshots_and_feedback_are_not_content(self):
        for rel in (".first/draft.md", "feedback.md", ".first/meta.json"):
            self.assertFalse(test_check_content.is_content_file(self.piece / rel, self.root), rel)
        self.assertTrue(test_check_content.is_content_file(self.piece / "draft.md", self.root))


class ReviewFixTests(unittest.TestCase):
    def setUp(self):
        self.tmp, self.root, self.piece = make_repo("review")
        self.addCleanup(self.tmp.cleanup)

    def test_pairs_captured_on_a_turn_already_blocked_are_still_reported(self):
        (self.piece / "draft.md").write_text("# T\n\nThe agent reads each ticket.\n", encoding="utf-8")
        test_check_content.decide_stop({}, self.root)
        (self.piece / "draft.md").write_text("# T\n\nThe agent reads and tags each ticket.\n", encoding="utf-8")
        set_status(self.root, "final")
        out = test_check_content.decide_stop({"stop_hook_active": True}, self.root)
        self.assertEqual(out["decision"], "block")
        self.assertIn("pairs.py label", out["reason"])
        self.assertIsNone(test_check_content.decide_stop({"stop_hook_active": True}, self.root), "asked once only")

    def test_pieces_from_before_first_versions_existed_get_no_snapshot(self):
        (self.root / "workspace" / "content-log.md").write_text(
            HEADER + "| 2026-11-24 | Old | LinkedIn post | review | `pieces/2026-11-25-agents/` | not yet |\n",
            encoding="utf-8")
        (self.piece / "draft.md").write_text(FIRST, encoding="utf-8")
        self.assertEqual(pairs.snapshot_ready(self.root), [])

    def test_running_pairs_py_is_not_an_edit_of_the_rules(self):
        import protect_rules
        command = 'python3 scripts/pairs.py feedback 2026-11-25-agents "keep the intro > 2 lines, cp the tone"'
        self.assertIsNone(protect_rules.decide({"tool_name": "Bash", "tool_input": {"command": command},
                                                "cwd": str(ROOT)}))
        edit = "sed -i '' 's/a/b/' scripts/pairs.py"
        out = protect_rules.decide({"tool_name": "Bash", "tool_input": {"command": edit}, "cwd": str(ROOT)})
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "ask", "editing pairs.py itself still asks")

class SecondReviewTests(unittest.TestCase):
    def test_a_skip_label_asks_and_feedback_and_list_do_not(self):
        import protect_rules
        ask = lambda c: protect_rules.decide({"tool_name": "Bash", "tool_input": {"command": c}, "cwd": str(ROOT)})  # noqa: E731
        self.assertEqual(ask('python3 scripts/pairs.py label x-1 --skip "fact"')["hookSpecificOutput"]["permissionDecision"], "ask")
        self.assertIsNone(ask('python3 scripts/pairs.py feedback x "a > b, cp it"'))
        self.assertIsNone(ask("python3 scripts/pairs.py list --unlabelled"))

    def test_a_run_of_rewrites_pairs_one_for_one(self):
        got = pairs.rewrites("A one.\n\nB one.\n\nC.", "A two.\n\nB two.\n\nC.")
        self.assertEqual(got, [("A one.", "A two."), ("B one.", "B two.")])

    def test_the_second_stop_saves_a_first_version_that_still_fails(self):
        tmp, root, piece = make_repo("review")
        self.addCleanup(tmp.cleanup)
        (piece / "draft.md").write_text("# T\n\nIt plays a pivotal role in the team.\n", encoding="utf-8")
        test_check_content.decide_stop({}, root)
        self.assertFalse((piece / pairs.FIRST_DIR / "meta.json").exists())
        test_check_content.decide_stop({"stop_hook_active": True}, root)
        self.assertTrue((piece / pairs.FIRST_DIR / "meta.json").exists())

if __name__ == "__main__":
    unittest.main()
