"""Offline tests for scripts/test_check_text.py and scripts/doctor.py. Run: python3 -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import test_check_text  # noqa: E402
import doctor  # noqa: E402


class CheckTextTests(unittest.TestCase):
    def test_dashes_are_errors(self):
        r = test_check_text.check("One idea \u2014 and another.\nA range 1\u20132.", banned=[])
        self.assertEqual(len(r["errors"]), 2)

    def test_banned_phrase_whole_word_and_curly_apostrophe(self):
        r = test_check_text.check("Honestly, here’s the thing about it.", banned=["here's the thing"])
        self.assertEqual(len(r["errors"]), 1)
        r = test_check_text.check("They unlocked the door.", banned=["unlock"])
        self.assertEqual(r["errors"], [])

    def test_contrast_formulas(self):
        for line in ["It's not a tool, it's a habit.", "This isn't just a note.", "Less talk, more work."]:
            self.assertTrue(test_check_text.check(line, banned=[])["errors"], line)
        self.assertFalse(test_check_text.check("It is a folder of notes.", banned=[])["errors"])

    def test_lesson_reveal_framing(self):
        for line in ["Here's what building it taught me about AI.", "## What I learnt",
                     "Three lessons I've learned this year.", "What we learned from it"]:
            self.assertTrue(test_check_text.check(line, banned=[])["errors"], line)
        for line in ["I learned Python last year.", "## What I'd pass on to anyone bringing AI into their team"]:
            self.assertFalse(test_check_text.check(line, banned=[])["errors"], line)

    def test_sentence_starting_with_here(self):
        for line in ["# I gave my company a brain. Here's how it changed things.", "Here is the plan.",
                     "Here are three lessons.", "And here is the twist.", "But here's why it matters.", "- **Here\u2019s why** it works", "Short version: here's the gist"]:
            self.assertTrue(test_check_text.check(line, banned=[])["errors"], line)
        for line in ["The notes live here.", "Everything is here, in one folder.", "Where is it? Right here.", "And here, the notes link up."]:
            self.assertFalse(test_check_text.check(line, banned=[])["errors"], line)

    def test_slogans(self):
        for line in ["## Three floors, one rule", "1 folder, 3 commands.", "## One ask, the week files itself"]:
            self.assertTrue(test_check_text.check(line, banned=[])["errors"], line)
        r = test_check_text.check("Private by default. Shared on purpose.", banned=[])
        self.assertEqual(r["errors"], [])
        self.assertTrue(any("slogan" in w for w in r["warnings"]))
        for line in ["You read it. You fix it.", "It has three floors and one rule.", "In 2024, 3 teams joined.", "One day, I found the old deck."]:
            r = test_check_text.check(line, banned=[])
            self.assertEqual(r["errors"], [], line)
            self.assertFalse(any("slogan" in w for w in r["warnings"]), line)

    def test_titles_starting_with_i_or_we(self):
        for line in ["# I built a shared context layer", "# I gave my company a brain", "## We tried three setups",
                     "# I've been building agents", "# \"I built it\""]:
            self.assertTrue(test_check_text.check(line, banned=[])["errors"], line)
        for line in ["# Shared context for agents is an operating model problem", "## Ideas for the roadmap",
                     "## In use", "I built it over a weekend, in Claude Code and Obsidian."]:
            self.assertEqual(test_check_text.check(line, banned=[])["errors"], [], line)

    def test_montage_of_fragments(self):
        montage = ("The strategy deck. The reason we picked vendor B over vendor A. The goal we agreed on in January "
                   "and quietly stopped talking about in March. It's all somewhere.")
        self.assertTrue(any("montage" in e for e in test_check_text.check(montage, banned=[])["errors"]))
        prose = ("The weekly skill pulls the week through your connectors. The skill writes your private note. "
                 "The lead runs the roll-up on Monday, and the summary lists whose update is missing.")
        self.assertFalse(any("montage" in e for e in test_check_text.check(prose, banned=[])["errors"]))

    def test_staccato_runs(self):
        self.assertTrue(any("staccato" in e for e in test_check_text.check(
            "You read it. You fix what it got wrong. You say yes. Only then is it published.", banned=[])["errors"]))
        for line in ["Google AI Studio's launch is cool. But I will stick to my stack. At least for now.",
                     "It works. The rest of the setup took a weekend, most of it spent on the sync folder.",
                     "| \"Which visuals?\" / \"Where?\" | `/plan-visuals` | `visual-handoff.md` |"]:
            self.assertFalse(any("staccato" in e for e in test_check_text.check(line, banned=[])["errors"]), line)

    def test_open_markers_are_warnings(self):
        r = test_check_text.check("Hi [CHECK: the date] and [YOUR MOMENT: why]. TBD.", banned=[])
        self.assertEqual(r["errors"], [])
        self.assertEqual(len(r["warnings"]), 3)

    def test_word_count_skips_markers_and_headings(self):
        text = "# Title here\n\nOne two three.\n\n[IMAGE v1: cover]\n"
        self.assertEqual(test_check_text.check(text, banned=[])["words"], 3)

    def test_post_section_only_is_counted(self):
        text = "# LinkedIn post\n\n**Status:** draft\n\n## Post\n\nOne two three four.\n\n## Other hooks to try\n\n1. Five six seven.\n"
        r = test_check_text.check(text, max_words=3, banned=[])
        self.assertEqual(r["words"], 4)
        self.assertIn("4 words, over the limit of 3", r["errors"])

    def test_markers_match_placement_map(self):
        draft = "Text.\n\n[IMAGE v1: cover]\n\n[IMAGE v2: floors]\n"
        visuals = "| id | slug |\n|---|---|\n| v1 | cover |\n| v3 | friday |\n"
        errors = test_check_text.check(draft, visuals_text=visuals, banned=[])["errors"]
        self.assertEqual(len(errors), 2)  # v2 has no row, v3 has no marker

    def test_template_rows_are_ignored(self):
        visuals = "| v1 | [slug] | [beat] |\n"
        self.assertEqual(test_check_text.check("Text.", visuals_text=visuals, banned=[])["errors"], [])

    def test_repo_banned_list_loads(self):
        self.assertIn("delve", test_check_text.load_banned())

    def test_repo_list_flags_explaining_down_and_selling(self):
        banned = test_check_text.load_banned()
        for line in ["## What it is, in plain words", "Simply put, it is a folder of notes.",
                     "No engineering needed.", "A cutting-edge, best-in-class setup.", "Excited to share my new repo."]:
            self.assertTrue(test_check_text.check(line, banned=banned)["errors"], line)
        for line in ["The agent fills its context window from the MCP server, then runs the evals.",
                     "I asked questions in plain language and watched the agents work.",
                     "Every note sits in plain text files.", "A note moves to the next level of the hierarchy."]:
            self.assertEqual(test_check_text.check(line, banned=banned)["errors"], [], line)


class DoctorTests(unittest.TestCase):
    def test_config_can_mark_a_sibling_optional(self):
        cfg = doctor.parse_config("repos:\n  site: ../site\n  tools: ../tools\noptional:\n  site: yes\n")
        self.assertEqual(doctor.optional_repos(cfg), {"company_brain", "site"})
        self.assertEqual(doctor.optional_repos({}), {"company_brain"})
        cfg = doctor.parse_config("repos:\n  site: ../site\noptional:\n  site: no\n")
        self.assertEqual(doctor.optional_repos(cfg), {"company_brain"})

    def test_parse_and_resolve(self):
        cfg = doctor.parse_config(
            "repos:\n  a: ../a   # comment\nprivate:\n  p: \"{a}/x.md\"\nlinks:\n  site: https://example.com\n"
        )
        paths = doctor.resolve(cfg, root=Path("/tmp/repo"))
        self.assertEqual(paths["a"], str(Path("/tmp/a").resolve()))
        self.assertEqual(paths["p"], str(Path("/tmp/a").resolve()) + "/x.md")
        self.assertEqual(paths["links.site"], "https://example.com")

    def test_repo_config_parses(self):
        cfg = doctor.parse_config(doctor.CONFIG.read_text(encoding="utf-8"))
        self.assertIn("design_assistant", cfg["repos"])
        self.assertIn("social_voice", doctor.resolve(cfg))


if __name__ == "__main__":
    unittest.main()
