"""The writing rules contract, writing-rules.yaml: this repo owns every writing rule and the user's voice.

A consumer repo finds the rules through the contract. These tests keep the contract true: schema 1, every rules: file present,
each key written once across writing-rules.yaml and config.yaml, the rules: files generic (no path
into workspace/, every {key} a contract key or {profile} and {rules}, which
every consumer has), the house rule IDs unique, and scripts/doctor.py resolving and checking the contract.
docs/writing-rules-contract.md explains the design.
Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import doctor  # noqa: E402
import test_rule_sync  # noqa: E402

CONTRACT = doctor.contract(ROOT)
CONFIG = doctor.parse_config((ROOT / "config.yaml").read_text(encoding="utf-8"))
KEY = re.compile(r"(?<![\w$])\{([a-z][a-z0-9_]*)\}")  # {social_voice}, not ${CLAUDE_PLUGIN_ROOT}
WORKSPACE_PATH = re.compile(r"(?<![\w./-])workspace/")
CONSUMER_KEYS = {"profile", "rules"}  # the user's profile and own rules: every consumer has them


def rules_files() -> dict[str, Path]:
    return {name: path for name, (section, path) in doctor.contract_paths(ROOT).items() if section == "rules"}


class ContractTests(unittest.TestCase):
    def test_schema_is_1(self):
        self.assertEqual(CONTRACT.get("schema"), "1")
        self.assertEqual(CONTRACT.get("provider"), "content-harness")

    def test_every_rules_path_exists(self):
        for name, path in rules_files().items():
            with self.subTest(key=name):
                self.assertTrue(path.is_file(), f"rules: {name} points to {path}, which does not exist")

    def test_paths_are_relative_to_the_repo(self):
        for section in doctor.CONTRACT_SECTIONS:
            for name, value in (CONTRACT.get(section) or {}).items():
                with self.subTest(key=name):
                    self.assertFalse(Path(value).is_absolute() or value.startswith(".."),
                                     f"{name} must be a path inside this repo: {value}")

    def test_rules_files_are_generic(self):
        # A rules file ships in a pack to people who cannot reach this repo: it points to a voice file or another
        # contract file by its key, never by a path,.
        for name, path in rules_files().items():
            for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                with self.subTest(key=name, line=no):
                    self.assertIsNone(WORKSPACE_PATH.search(line), f"{path.name}:{no} names a path into workspace/: "
                                      f"use the voice key in braces instead: {line.strip()[:80]}")

    def test_every_key_in_a_rules_file_is_a_contract_key(self):
        known = set(doctor.contract_paths(ROOT)) | CONSUMER_KEYS
        for name, path in rules_files().items():
            with self.subTest(key=name):
                unknown = sorted(set(KEY.findall(path.read_text(encoding="utf-8"))) - known)
                self.assertEqual(unknown, [], f"{path.name} uses keys that are not in writing-rules.yaml: {unknown}")

    def test_no_key_is_in_both_files(self):
        self.assertEqual(doctor.restated_keys(CONFIG, ROOT), [],
                         "a contract key is written in config.yaml too: keep it in writing-rules.yaml only")

    def test_house_rule_ids_are_unique(self):
        text = (ROOT / "system" / "00-core" / "house-rules.md").read_text(encoding="utf-8")
        ids = [m.group(2) for m in map(test_rule_sync.RULE_LINE.match, text.splitlines()) if m]
        self.assertTrue(ids)
        self.assertEqual(len(ids), len(set(ids)), "a rule ID is used twice in house-rules.md")

    def test_doctor_reports_no_problem_for_this_repo(self):
        self.assertEqual(doctor.contract_problems(CONFIG, ROOT), [])


class DoctorTests(unittest.TestCase):
    def layout(self, contract: str, config: str = "private:\n  profile: \"x/MY_PROFILE.md\"\n"):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        (root / doctor.CONTRACT_NAME).write_text(contract, encoding="utf-8")
        (root / "config.yaml").write_text(config, encoding="utf-8")
        (root / "rules.md").write_text("# Rules\n", encoding="utf-8")
        return tmp, root, doctor.parse_config(config)

    def test_contract_keys_resolve_to_paths_in_the_repo(self):
        tmp, root, config = self.layout("schema: 1\nprovider: p\nrules:\n  house_rules: rules.md\n"
                                        "voice:\n  social_voice: workspace/v/SOCIAL_VOICE.md\n")
        with tmp:
            paths = doctor.resolve(config, root)
            self.assertEqual(paths["house_rules"], str(root / "rules.md"))
            self.assertEqual(paths["social_voice"], str(root / "workspace" / "v" / "SOCIAL_VOICE.md"))
            self.assertEqual(doctor.contract_problems(config, root), [])

    def test_a_missing_rules_file_is_reported_and_a_missing_voice_file_is_not(self):
        tmp, root, config = self.layout("schema: 1\nprovider: p\nrules:\n  house_rules: rules.md\n"
                                        "  cv_rules: gone.md\nvoice:\n  social_voice: not/yet.md\n")
        with tmp:
            problems = doctor.contract_problems(config, root)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("cv_rules", problems[0])

    def test_an_unknown_schema_is_reported(self):
        tmp, root, config = self.layout("schema: 2\nprovider: p\nrules:\n  house_rules: rules.md\n")
        with tmp:
            self.assertTrue(any("schema 2" in p for p in doctor.contract_problems(config, root)))

    def test_a_key_in_both_files_is_reported(self):
        tmp, root, config = self.layout("schema: 1\nprovider: p\nrules:\n  house_rules: rules.md\n"
                                        "voice:\n  social_voice: v.md\n",
                                        "private:\n  social_voice: \"elsewhere/SOCIAL_VOICE.md\"\n"
                                        "rule_mirrors:\n  social_voice: \"{social_voice}\"\n")
        with tmp:
            problems = doctor.contract_problems(config, root)
        self.assertEqual([p for p in problems if "both" in p], [
            "social_voice is in both writing-rules.yaml and config.yaml: keep it in writing-rules.yaml only"])

    def test_a_repo_without_a_contract_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(doctor.contract_problems({}, Path(tmp)),
                             ["writing-rules.yaml is missing: the writing rules have no contract"])


if __name__ == "__main__":
    unittest.main()
