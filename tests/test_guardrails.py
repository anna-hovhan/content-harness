"""Offline tests for the guardrail scripts: the rule-file hook and the piece checker.

Run: python3 -m unittest discover -s tests
"""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import test_check_pieces  # noqa: E402
import test_check_structure  # noqa: E402
import doctor  # noqa: E402
import test_rule_sync  # noqa: E402
import protect_rules  # noqa: E402


def decision(tool, **tool_input):
    out = protect_rules.decide({"tool_name": tool, "tool_input": tool_input, "cwd": str(ROOT)})
    return out["hookSpecificOutput"]["permissionDecision"] if out else "pass"


class ProtectRulesHookTests(unittest.TestCase):
    def test_file_tools_on_rule_files_ask(self):
        self.assertEqual(decision("Edit", file_path=str(ROOT / "system/00-core/house-rules.md")), "ask")
        self.assertEqual(decision("Write", file_path="tests/rules.lock"), "ask")
        self.assertEqual(decision("Edit", file_path=str(ROOT / "AGENTS.md")), "ask")

    def test_file_tools_on_pieces_pass(self):
        self.assertEqual(decision("Edit", file_path=str(ROOT / "workspace/content-log.md")), "pass")
        self.assertEqual(decision("Write", file_path="/tmp/elsewhere/house-rules.md"), "pass")

    def test_shell_writes_to_rule_files_ask(self):
        for command in ["sed -i /x/d system/00-core/banned-phrases.txt",
                        "echo x >> system/00-core/banned-phrases.txt",
                        "git checkout -- AGENTS.md",
                        "python3 - <<EOF\nPath('scripts/test_check_text.py').write_text('')\nEOF"]:
            self.assertEqual(decision("Bash", command=command), "ask", command)

    def test_shell_reads_and_checker_runs_pass(self):
        for command in ["python3 scripts/test_check_text.py draft.md --visuals visuals.md 2>&1 | tail -3",
                        "cp draft.md article.md && python3 ../../../scripts/test_check_text.py draft.md",
                        "grep -n slogan system/00-core/house-rules.md",
                        "python3 -m unittest discover -s tests 2>&1 | tail -3",
                        "git diff system/00-core/house-rules.md > /dev/null"]:
            self.assertEqual(decision("Bash", command=command), "pass", command)


class CheckPiecesTests(unittest.TestCase):
    LOG = ("| Date | Piece | Channel | Status | Folder | Published at |\n|---|---|---|---|---|---|\n"
           "| 2026-11-09 | A | LinkedIn article | review: second pass | `pieces/a/` | not yet |\n"
           "| 2026-11-07 | B | LinkedIn post | parked: replaced | `pieces/b/` | not yet |\n")

    def test_log_rows(self):
        rows = test_check_pieces.log_rows(self.LOG)
        self.assertEqual([(r["status"], r["folder"]) for r in rows], [("review", "pieces/a/"), ("parked", "pieces/b/")])

    def test_repo_pieces_in_review_or_later_pass(self):
        self.assertEqual(test_check_pieces.main([]), 0)

    def test_the_voice_library_is_never_checked(self):
        # The user's published posts are kept exactly as written, dashes included; even a log row that points
        # into workspace/tone-of-voice/ must not run the copy checks on them.
        self.assertTrue(test_check_pieces.is_voice_library("tone-of-voice/social/"))
        self.assertFalse(test_check_pieces.is_voice_library("pieces/2026-01-01-post/"))
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            social = workspace / "tone-of-voice" / "social"
            social.mkdir(parents=True)
            (social / "draft.md").write_text("A post — as published.\n", encoding="utf-8")
            log = workspace / "content-log.md"
            log.write_text("| Date | Piece | Channel | Status | Folder | Published at |\n|---|---|---|---|---|---|\n"
                           "| 2026-11-09 | A post | LinkedIn post | posted | `tone-of-voice/social/` | live |\n",
                           encoding="utf-8")
            with mock.patch.object(test_check_pieces, "LOG", log), redirect_stdout(io.StringIO()) as out:
                self.assertEqual(test_check_pieces.main(["--all"]), 0)
        self.assertIn("skip     tone-of-voice/social/ (the voice library", out.getvalue())


class CheckStructureTests(unittest.TestCase):
    def test_ledger_row_numbers_do_not_trace_a_number(self):
        evidence = ("## Facts\n\n| # | Claim | Source | As of |\n|---|---|---|---|\n"
                    + "".join(f"| {n} | claim | `f.md` | |\n" for n in range(1, 45)))
        errors = test_check_structure.check(None, evidence, "It has 40 skills.\n")["errors"]
        self.assertTrue(any("'40'" in e for e in errors), errors)

    def test_links_need_a_check_date(self):
        evidence = ("## Facts\n\n| # | Claim | Source | As of |\n|---|---|---|---|\n| 1 | c | s | |\n\n"
                    "## Links the piece may use\n\n| Link | Public and live? | Checked |\n|---|---|---|\n| github.com/a/b | yes | |\n")
        errors = test_check_structure.check(None, evidence, "github.com/a/b\n")["errors"]
        self.assertIn("links: 'github.com/a/b' has no check date in the links table", errors)

    def test_file_names_and_markers_are_not_links_or_numbers(self):
        evidence = "## Facts\n\n| # | Claim | Source | As of |\n|---|---|---|---|\n| 1 | c | s | |\n"
        piece = "[IMAGE v2: layers]\n\nIts `ROADMAP.md` lists the gaps. Weekly 1:1s stay private.\n"
        self.assertEqual(test_check_structure.check(None, evidence, piece)["errors"], ["brief: no brief.md"])

    def test_posts_need_no_limits_section(self):
        errors = test_check_structure.check(None, None, "A post.\n", "LinkedIn post")["errors"]
        self.assertFalse(any(e.startswith("limits:") for e in errors), errors)

    def test_blog_posts_need_no_limits_section_but_articles_and_pages_do(self):
        # The user's writing rules of 2026-11-25: a blog post keeps its limits to a sentence or two, or none.
        def limits(channel):
            return any(e.startswith("limits:") for e in test_check_structure.check(None, None, "Text.\n", channel)["errors"])
        self.assertFalse(limits("Portfolio blog article"))
        self.assertTrue(limits("LinkedIn article"))
        self.assertTrue(limits("Portfolio page"))

    def test_blog_word_cap_applies_from_2026_11_25_only(self):
        # A 4-minute read on the site is at most 880 words; posts published before the rule are left as they are.
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            for name in ("2026-11-24-old-blog-post", "2026-11-25-new-blog-post"):
                (ws / name).mkdir()
                (ws / name / "article.md").write_text("# Title\n\n" + "word " * 900 + "\n", encoding="utf-8")
            def capped(date, name):
                _, result = test_check_pieces.check_piece(
                    {"date": date, "piece": "p", "channel": "Portfolio blog article", "status": "final", "folder": name}, ws)
                return any("880" in e for e in result["errors"])
            self.assertFalse(capped("2026-11-24", "2026-11-24-old-blog-post"))
            self.assertTrue(capped("2026-11-25", "2026-11-25-new-blog-post"))

    def test_open_markers_warn_in_review_and_fail_once_final(self):
        self.assertTrue(test_check_structure.check(None, None, "[CHECK: x]\n", "", "review")["warnings"])
        self.assertIn("open marker: [CHECK: x] in a piece marked final",
                      test_check_structure.check(None, None, "[CHECK: x]\n", "", "final")["errors"])

    def test_hook_protects_the_structure_check(self):
        self.assertEqual(decision("Edit", file_path="scripts/test_check_structure.py"), "ask")
        self.assertEqual(decision("Bash", command="python3 scripts/test_check_structure.py workspace/pieces/x"), "pass")


class RuleSyncTests(unittest.TestCase):
    KNOWN = {"HR-no-dashes": "No em dashes or en dashes", "HR-no-cinematic-openings": "No cinematic or dramatic openings."}

    def test_house_rule_ids_parse(self):
        ids = test_rule_sync.house_rule_ids()
        self.assertEqual(ids["HR-no-dashes"], "No em dashes or en dashes")
        self.assertEqual(ids["HR-no-cinematic-openings"], "No cinematic or dramatic openings.")

    def test_a_copy_that_names_its_id_is_clean(self):
        text = "- No staccato runs of short sentences (`HR-no-cinematic-openings`).\n- No em dashes. `HR-no-dashes`\n"
        self.assertEqual(test_rule_sync.scan(text, self.KNOWN), {"unknown": [], "uncited": [], "untagged": []})

    def test_a_copy_without_its_id_is_reported(self):
        report = test_rule_sync.scan("Avoid staccato: three short sentences in a row.\n", self.KNOWN)
        self.assertEqual(len(report["uncited"]), 1)
        self.assertIn("HR-no-cinematic-openings", report["uncited"][0])

    def test_an_id_the_source_lost_is_reported(self):
        report = test_rule_sync.scan("- No dashes (`HR-no-hyphens`).\n", self.KNOWN)
        self.assertIn("HR-no-hyphens", report["unknown"][0])

    def test_a_rule_only_this_file_has_is_reported(self):
        report = test_rule_sync.scan("- **No hashtags** in posts.\n", self.KNOWN)
        self.assertEqual(len(report["untagged"]), 1)

    def test_doctor_resolves_the_mirrors(self):
        config = doctor.parse_config((ROOT / "config.yaml").read_text(encoding="utf-8"))
        mirrors = doctor.rule_mirrors(config, doctor.resolve(config))
        self.assertEqual(mirrors["agents"], ROOT / "AGENTS.md")
        self.assertTrue(str(mirrors["social_voice_rules"]).endswith("social-voice-rules.md"))
        self.assertNotIn("{", "".join(str(p) for p in mirrors.values()))

    def test_hook_protects_rule_sync(self):
        self.assertEqual(decision("Write", file_path="scripts/test_rule_sync.py"), "ask")


if __name__ == "__main__":
    unittest.main()
