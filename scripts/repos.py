#!/usr/bin/env python3
"""Keep the sibling repos in config.yaml present and up to date, from their git URLs.

Usage:
  python3 scripts/repos.py status            # each repo: present?, branch, clean?, behind its remote?
  python3 scripts/repos.py clone [NAME ...]  # clone the missing ones into their configured paths
  python3 scripts/repos.py pull [NAME ...]   # fast-forward the ones already there
  python3 scripts/repos.py sync [NAME ...]   # clone what is missing, then pull the rest

Safe by design:
- pull only fast-forwards (git pull --ff-only), and skips a repo with uncommitted changes,
  a detached HEAD or no upstream, saying why. It never merges, rebases, resets or pushes.
- clone never writes into a folder that already exists.
- Credentials are git's own: your usual GitHub login on a laptop, the session's git
  access in a cloud session (where a private repo must be attached to the session).

Exit 1 when a required repo is still missing or a git command failed.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import doctor  # noqa: E402

OPTIONAL = doctor.OPTIONAL_REPOS


def optional(name: str) -> bool:
    """True for a repo this install runs without: built in, or marked yes under optional: in config.yaml."""
    try:
        config = doctor.parse_config(doctor.CONFIG.read_text(encoding="utf-8"))
    except OSError:
        config = {}
    return name in doctor.optional_repos(config)


def git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def split_url(spec: str) -> tuple[str, str | None]:
    """'https://host/owner/repo@branch' -> (url, branch). An '@' inside user@host is not a branch."""
    head, sep, tail = spec.rpartition("@")
    if sep and "/" not in tail and "/" in head and not head.endswith(":"):
        return head, tail
    return spec, None


def targets(config: dict, names: list[str]) -> list[tuple[str, Path, str | None, str | None]]:
    paths = doctor.resolve(config)
    remotes = config.get("git", {})
    unknown = [n for n in names if n not in config.get("repos", {})]
    if unknown:
        sys.exit(f"unknown repo name(s): {', '.join(unknown)}. Known: {', '.join(config.get('repos', {}))}")
    out = []
    for name in names or list(config.get("repos", {})):
        url, branch = split_url(remotes[name]) if name in remotes else (None, None)
        out.append((name, Path(paths[name]), url, branch))
    return out


def repo_state(path: Path) -> dict:
    if not (path / ".git").exists():
        return {"present": path.exists(), "git": False}
    branch = git("symbolic-ref", "--quiet", "--short", "HEAD", cwd=path).stdout.strip()
    dirty = bool(git("status", "--porcelain", cwd=path).stdout.strip())
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", cwd=path)
    behind = None
    if upstream.returncode == 0:
        counts = git("rev-list", "--count", "--left-right", "HEAD...@{u}", cwd=path).stdout.split()
        if len(counts) == 2:
            behind = int(counts[1])
    return {"present": True, "git": True, "branch": branch or None, "dirty": dirty,
            "upstream": upstream.stdout.strip() if upstream.returncode == 0 else None, "behind": behind}


def clone(name: str, path: Path, url: str | None, branch: str | None) -> bool:
    if path.exists():
        print(f"  skip     {name}: {path} already exists")
        return True
    if not url:
        print(f"  MISSING  {name}: no git URL for it in config.yaml")
        return False
    args = ["clone", url, str(path)] + (["--branch", branch] if branch else [])
    r = git(*args)
    if r.returncode != 0:
        print(f"  FAILED   {name}: git clone {url}\n           {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ''}")
        print("           In a cloud session a private repo must be attached to the session first.")
        return False
    print(f"  cloned   {name} into {path}")
    return True


def pull(name: str, path: Path) -> bool:
    s = repo_state(path)
    if not s["present"]:
        print(f"  missing  {name}: run 'python3 scripts/repos.py clone {name}'")
        return optional(name)
    if not s["git"]:
        print(f"  skip     {name}: {path} is not a git repo")
        return True
    if s["dirty"]:
        print(f"  skip     {name}: uncommitted changes; commit or stash them, then pull")
        return True
    if not s["branch"] or not s["upstream"]:
        print(f"  skip     {name}: {'detached HEAD' if not s['branch'] else 'no upstream branch'}")
        return True
    r = git("pull", "--ff-only", "--quiet", cwd=path)
    if r.returncode != 0:
        print(f"  FAILED   {name}: cannot fast-forward {s['branch']} (it has diverged from {s['upstream']}); resolve it in that repo")
        return False
    after = git("log", "-1", "--format=%h %s", cwd=path).stdout.strip()
    print(f"  ok       {name} ({s['branch']}): {after[:70]}")
    return True


def status(name: str, path: Path, url: str | None) -> bool:
    s = repo_state(path)
    if not s["present"]:
        tag = "optional, missing" if optional(name) else "MISSING"
        print(f"  {tag:18} {name:20} clone with: python3 scripts/repos.py clone {name}")
        return optional(name)
    if not s["git"]:
        print(f"  {'not a git repo':18} {name:20} {path}")
        return True
    git("fetch", "--quiet", cwd=path)
    s = repo_state(path)
    notes = [s["branch"] or "detached HEAD"]
    if s["dirty"]:
        notes.append("uncommitted changes")
    if s["behind"]:
        notes.append(f"{s['behind']} commit(s) behind {s['upstream']}")
    print(f"  {'ok':18} {name:20} {', '.join(notes)}")
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("action", choices=["status", "clone", "pull", "sync"])
    ap.add_argument("names", nargs="*")
    args = ap.parse_args(argv)

    config = doctor.parse_config(doctor.CONFIG.read_text(encoding="utf-8"))
    ok = True
    for name, path, url, branch in targets(config, args.names):
        if args.action == "status":
            ok &= status(name, path, url)
        elif args.action == "clone":
            ok &= clone(name, path, url, branch) or optional(name)
        elif args.action == "pull":
            ok &= pull(name, path)
        else:  # sync
            ok &= (clone(name, path, url, branch) or optional(name)) if not path.exists() else pull(name, path)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
