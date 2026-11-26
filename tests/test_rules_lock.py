"""The rules lock: rules may change only together with tests/rules.lock, and checks may never get weaker.

Run: python3 -m unittest discover -s tests
"""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import test_check_structure  # noqa: E402
import test_check_text  # noqa: E402
import test_rule_sync  # noqa: E402

LOCK = json.loads((ROOT / "tests" / "rules.lock").read_text(encoding="utf-8"))
HOUSE_RULES = ROOT / "system" / "00-core" / "house-rules.md"
CASES = ROOT / "tests" / "feedback" / "cases.json"
HOW = "Change tests/rules.lock in the same commit, with the user's yes."


def house_rule_names() -> list[str]:
    return re.findall(r"^- \*\*(.+?)\*\*", HOUSE_RULES.read_text(encoding="utf-8"), re.M)


# A piece folder that went through the loop: brief, evidence, piece, channel, log status.
GOOD_PIECE = (
    "# Brief: X\n\n**Status:** review\n\n## Reader\n\n- **Who:** platform engineers\n"
    "- **Their question:** how does it hold up?\n\n## Takeaway\n\nA takeaway.\n\n"
    "## Terms table\n\n| Term in the sources | Term in the piece | Gloss |\n|---|---|---|\n| vault | vault | |\n",
    "# Evidence\n\n## Facts\n\n| # | Claim | Source | As of |\n|---|---|---|---|\n"
    "| 1 | It ships 32 skills | `README.md` | 2026-11-10 |\n\n## Links the piece may use\n\n"
    "| Link | Public and live? | Checked |\n|---|---|---|\n| github.com/a/b | yes | 2026-11-10 |\n",
    "# Shared context\n\nIt ships 32 skills.\n\n## Limitations\n\nA prototype.\n\ngithub.com/a/b\n",
    "LinkedIn article", "review")
# One way to break the piece for each locked structure error.
STRUCTURE_BREAKS = {
    "brief": lambda b, e, p, c, s: (b.replace("A takeaway.", ""), e, p, c, s),
    "evidence": lambda b, e, p, c, s: (b, None, p, c, s),
    "trace": lambda b, e, p, c, s: (b, e, p.replace("32 skills", "40 skills"), c, s),
    "links": lambda b, e, p, c, s: (b, e, p + "\nhttps://example.com/x\n", c, s),
    "limits": lambda b, e, p, c, s: (b, e, p.replace("## Limitations", "## Notes"), c, s),
    "status": lambda b, e, p, c, s: (b, e, p, c, "drafting"),
    "open marker": lambda b, e, p, c, s: (b.replace("review", "final"), e, p + "\n[CHECK: x]\n", c, "final"),
}


class RulesLockTests(unittest.TestCase):
    def test_house_rules_match_the_lock(self):
        current, locked = set(house_rule_names()), set(LOCK["house_rules"])
        self.assertFalse(locked - current, f"house rules removed or renamed: {sorted(locked - current)}. {HOW}")
        self.assertFalse(current - locked, f"new house rules not in the lock yet: {sorted(current - locked)}. {HOW}")

    def test_rule_ids_match_the_lock(self):
        text = HOUSE_RULES.read_text(encoding="utf-8")
        current, locked = test_rule_sync.house_rule_ids(text), LOCK["rule_ids"]
        all_ids = test_rule_sync.ID.findall(text)
        self.assertEqual(len(all_ids), len(set(all_ids)), f"a rule ID is used twice in house-rules.md: {sorted(all_ids)}")
        self.assertFalse(set(locked) - set(current), f"rule IDs removed or renamed: {sorted(set(locked) - set(current))}. {HOW}")
        self.assertFalse(set(current) - set(locked), f"new rule IDs not in the lock yet: {sorted(set(current) - set(locked))}. {HOW}")
        moved = {rid: (locked[rid], current[rid]) for rid in locked if rid in current and locked[rid] != current[rid]}
        self.assertFalse(moved, f"a rule ID now sits on another rule: {moved}. {HOW}")

    def test_agents_md_names_the_id_of_every_rule_it_restates(self):
        report = test_rule_sync.scan((ROOT / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertEqual(report, {"unknown": [], "uncited": [], "untagged": []},
                         "AGENTS.md restates a house rule without its HR- ID, or names an ID house-rules.md no longer has")

    def test_banned_phrases_match_the_lock(self):
        current, locked = set(test_check_text.load_banned()), set(LOCK["banned_phrases"])
        self.assertFalse(locked - current, f"banned phrases removed: {sorted(locked - current)}. {HOW}")
        self.assertFalse(current - locked, f"new banned phrases not in the lock yet: {sorted(current - locked)}. {HOW}")

    def test_every_locked_error_type_is_still_an_error(self):
        for name, case in LOCK["checker_errors"].items():
            with self.subTest(error=name):
                result = test_check_text.check(case["text"], case.get("max_words"), case.get("visuals"))
                self.assertTrue(any(case["contains"] in e for e in result["errors"]),
                                f"'{name}' no longer raises an error containing '{case['contains']}': "
                                f"errors {result['errors']}, warnings {result['warnings']}")

    def test_every_locked_structure_error_is_still_an_error(self):
        missing = set(LOCK["structure_errors"]) - set(STRUCTURE_BREAKS)
        self.assertFalse(missing, f"no broken piece for locked structure errors {sorted(missing)}: add one to STRUCTURE_BREAKS")
        self.assertEqual(test_check_structure.check(*GOOD_PIECE)["errors"], [], "the well-formed piece must pass")
        for name in LOCK["structure_errors"]:
            with self.subTest(error=name):
                errors = test_check_structure.check(*STRUCTURE_BREAKS[name](*GOOD_PIECE))["errors"]
                self.assertTrue(any(e.startswith(name + ":") for e in errors),
                                f"structure error '{name}' no longer fires: {errors}")

    def test_feedback_cases_are_never_removed(self):
        ids = {c["id"] for c in json.loads(CASES.read_text(encoding="utf-8"))["cases"]}
        missing = set(LOCK["feedback_cases"]) - ids
        self.assertFalse(missing, f"feedback cases removed from tests/feedback/cases.json: {sorted(missing)}")


if __name__ == "__main__":
    unittest.main()
