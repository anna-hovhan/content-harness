#!/usr/bin/env python3
"""Check that the sibling repos, the private files and the writing rules this repo names exist.

Two files name them. config.yaml holds the sibling repos and the user's facts that another repo owns
(profile, goals, rules, master CV, stories). writing-rules.yaml is the writing rules contract: every key
of a writing rule or a voice file this repo owns, as a path relative to the repo (docs/writing-rules-contract.md).
Workflows refer to the keys of both in braces ({social_voice}, {design_assistant}); resolve() reads both.

Usage:
  python3 scripts/doctor.py            # report
  python3 scripts/doctor.py --json     # resolved paths, for other scripts
  python3 scripts/doctor.py --get KEY  # print one resolved path (e.g. --get social_voice)

Exit 1 when a repo is missing, when a file under rule_mirrors: names a house-rule ID that house-rules.md
no longer has, or when the contract is broken: a rules: file missing, a schema other than 1, or a key in
both files. Private files and voice files that are missing are warnings: a module that needs one says so
when it runs. Rule copies without their ID are warnings (scripts/test_rule_sync.py).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.yaml"
CONTRACT_NAME = "writing-rules.yaml"
CONTRACT_SCHEMA = "1"
CONTRACT_SECTIONS = ("rules", "voice")
OPTIONAL_REPOS = {"company_brain"}


def optional_repos(config: dict[str, dict[str, str]]) -> set[str]:
    """Repos this install can run without: the built-in ones and those config.yaml marks `yes` under optional:."""
    listed = config.get("optional", {})
    return OPTIONAL_REPOS | {name for name, value in listed.items() if value.strip().lower() in ("yes", "true")}
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_rule_sync  # noqa: E402


def parse_config(text: str) -> dict[str, dict[str, str]]:
    """Read the two-level 'section:\\n  key: value' subset of YAML that config.yaml uses."""
    config: dict[str, dict[str, str]] = {}
    section = None
    for raw in text.splitlines():
        line = re.sub(r"\s+#.*$", "", raw) if not raw.lstrip().startswith("#") else ""
        if not line.strip():
            continue
        if not line.startswith(" "):
            section = line.rstrip(":").strip()
            config[section] = {}
        elif section is not None:
            key, _, value = line.strip().partition(":")
            config[section][key.strip()] = value.strip().strip('"').strip("'")
    return config


def parse_contract(text: str) -> dict:
    """Read writing-rules.yaml: top-level `key: value` lines (schema, provider) and two-level sections
    (rules:, voice:), the same YAML subset as config.yaml."""
    out: dict = {}
    section = None
    for raw in text.splitlines():
        line = re.sub(r"\s+#.*$", "", raw) if not raw.lstrip().startswith("#") else ""
        if not line.strip():
            continue
        key, _, value = line.strip().partition(":")
        value = value.strip().strip('"').strip("'")
        if not line.startswith(" "):
            section = None if value else key.strip()
            out[key.strip()] = value if value else {}
        elif section is not None:
            out[section][key.strip()] = value
    return out


def contract(root: Path = ROOT) -> dict:
    """The writing rules contract of the repo at root, or {} when it has none."""
    path = root / CONTRACT_NAME
    return parse_contract(path.read_text(encoding="utf-8")) if path.is_file() else {}


def contract_paths(root: Path = ROOT) -> dict[str, tuple[str, Path]]:
    """{key: (section, path)} for every key of the contract, each path relative to root made absolute."""
    out: dict[str, tuple[str, Path]] = {}
    c = contract(root)
    for section in CONTRACT_SECTIONS:
        for name, value in (c.get(section) or {}).items():
            p = Path(value)
            out[name] = (section, p if p.is_absolute() else root / p)
    return out


def restated_keys(config: dict[str, dict[str, str]], root: Path = ROOT) -> list[str]:
    """Contract keys that config.yaml also defines as a path. rule_mirrors: only names files to scan."""
    defined = {k for section in ("repos", "private", "references") for k in config.get(section, {})}
    return sorted(set(contract_paths(root)) & defined)


def contract_problems(config: dict[str, dict[str, str]], root: Path = ROOT) -> list[str]:
    """What breaks the contract: no writing-rules.yaml, a schema other than 1, a rules: file that is
    missing, or a key that config.yaml restates."""
    if not (root / CONTRACT_NAME).is_file():
        return [f"{CONTRACT_NAME} is missing: the writing rules have no contract"]
    c = contract(root)
    problems = []
    if c.get("schema") != CONTRACT_SCHEMA:
        problems.append(f"{CONTRACT_NAME} has schema {c.get('schema') or 'none'}; this repo reads schema {CONTRACT_SCHEMA}")
    for name, (section, path) in contract_paths(root).items():
        if section == "rules" and not path.is_file():
            problems.append(f"rules: {name} points to {path}, which does not exist")
    for name in restated_keys(config, root):
        problems.append(f"{name} is in both {CONTRACT_NAME} and config.yaml: keep it in {CONTRACT_NAME} only")
    return problems


def resolve(config: dict[str, dict[str, str]], root: Path = ROOT) -> dict[str, str]:
    """Flatten the config and the writing rules contract, and expand {key} references and relative paths.
    A contract key wins over a key of the same name in config.yaml, which contract_problems reports."""
    flat: dict[str, str] = {}
    for name, path in config.get("repos", {}).items():
        p = Path(path)
        p = (root / p).resolve() if not p.is_absolute() else p
        if not p.exists() and p.parent.is_dir():  # a clone named Portfolio or portfolio
            match = [c for c in p.parent.iterdir() if c.name.lower() == p.name.lower()]
            p = match[0] if match else p
        flat[name] = str(p)
    for section in ("private", "references"):
        for name, value in config.get(section, {}).items():
            flat[name] = value
    for name, (_, path) in contract_paths(root).items():
        flat[name] = str(path)
    for name, value in config.get("links", {}).items():
        flat[f"links.{name}"] = value
    for _ in range(5):  # nested references
        for name, value in flat.items():
            flat[name] = re.sub(r"\{([\w.]+)\}", lambda m: flat.get(m.group(1), m.group(0)), value)
    return flat


def rule_mirrors(config: dict[str, dict[str, str]], paths: dict[str, str], root: Path = ROOT) -> dict[str, Path]:
    """The files that restate house rules, resolved like the other paths."""
    out = {}
    for name, value in config.get("rule_mirrors", {}).items():
        value = re.sub(r"\{([\w.]+)\}", lambda m: paths.get(m.group(1), m.group(0)), value)
        p = Path(value)
        out[name] = p if p.is_absolute() else root / p
    return out


def report_rule_mirrors(mirrors: dict[str, Path]) -> bool:
    """Print the rule-ID scan per mirror. True when a mirror names an ID the house rules no longer have."""
    known = test_rule_sync.house_rule_ids()
    drift = False
    print("Rule copies (IDs from house-rules.md)")
    for name, path in mirrors.items():
        if not path.is_file():
            print(f"  {'not found':18} {name:20} {path}")
            continue
        report = test_rule_sync.scan(path.read_text(encoding="utf-8"), known)
        drift |= bool(report["unknown"])
        counts = {k: len(v) for k, v in report.items()}
        tag = "ok" if not any(counts.values()) else ("DRIFT" if counts["unknown"] else "check")
        print(f"  {tag:18} {name:20} {counts['unknown']} unknown ID, {counts['uncited']} without ID, {counts['untagged']} untagged")
        for kind in ("unknown", "uncited", "untagged"):
            for item in report[kind]:
                print(f"      {kind:9} {item}")
    return drift


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--get")
    args = ap.parse_args(argv)

    config = parse_config(CONFIG.read_text(encoding="utf-8"))
    paths = resolve(config)

    if args.get:
        if args.get not in paths:
            print(f"unknown key: {args.get}", file=sys.stderr)
            return 2
        print(paths[args.get])
        return 0
    if args.json:
        print(json.dumps(paths, indent=2))
        return 0

    missing_repo = False
    optional = optional_repos(config)
    print("Repos")
    for name in config.get("repos", {}):
        ok = Path(paths[name]).is_dir()
        tag = "ok" if ok else ("optional, missing" if name in optional else "MISSING")
        missing_repo |= not ok and name not in optional
        print(f"  {tag:18} {name:20} {paths[name]}")
    for section in ("private", "references"):
        print(section.capitalize())
        for name in config.get(section, {}):
            ok = Path(paths[name]).exists()
            print(f"  {'ok' if ok else 'missing':18} {name:20} {paths[name]}")
    print(f"Writing rules ({CONTRACT_NAME})")
    for name, (section, path) in contract_paths().items():
        tag = "ok" if path.exists() else ("MISSING" if section == "rules" else "missing")
        print(f"  {tag:18} {name:20} {path}")
    broken = contract_problems(config)
    drift = report_rule_mirrors(rule_mirrors(config, paths))
    if missing_repo:
        print("\nA required repo is missing: run python3 scripts/repos.py clone, or fix its path in config.yaml.")
    if broken:
        print(f"\nThe writing rules contract is broken ({CONTRACT_NAME}, docs/writing-rules-contract.md):")
        for problem in broken:
            print(f"  {problem}")
    if drift:
        print("\nA rule copy names an ID house-rules.md no longer has: update the copy, or the house rules, with the user.")
    return 1 if missing_repo or drift or broken else 0


if __name__ == "__main__":
    sys.exit(main())
