"""Offline tests for scripts/repos.py: clones and fast-forwards a throwaway local repo."""
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import doctor  # noqa: E402
import repos  # noqa: E402


def run(*args, cwd=None):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def commit(folder: Path, name: str):
    (folder / name).write_text(name)
    run("add", name, cwd=folder)
    run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", name, cwd=folder)


class SplitUrlTests(unittest.TestCase):
    def test_branch_suffix(self):
        self.assertEqual(repos.split_url("https://github.com/a/b@dev"), ("https://github.com/a/b", "dev"))
        self.assertEqual(repos.split_url("https://github.com/a/b"), ("https://github.com/a/b", None))
        self.assertEqual(repos.split_url("git@github.com:a/b.git"), ("git@github.com:a/b.git", None))

    def test_repo_config_has_a_url_for_every_repo(self):
        cfg = doctor.parse_config(doctor.CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(set(cfg["git"]), set(cfg["repos"]))


class CloneAndPullTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.origin = base / "origin"
        self.origin.mkdir()
        run("init", "-q", "-b", "main", cwd=self.origin)
        commit(self.origin, "one.txt")
        self.target = base / "clone"

    def tearDown(self):
        self.tmp.cleanup()

    def quiet(self, fn, *args):
        with redirect_stdout(StringIO()) as out:
            result = fn(*args)
        return result, out.getvalue()

    def test_clone_then_fast_forward(self):
        ok, _ = self.quiet(repos.clone, "x", self.target, str(self.origin), None)
        self.assertTrue(ok and (self.target / "one.txt").exists())
        commit(self.origin, "two.txt")
        ok, _ = self.quiet(repos.pull, "x", self.target)
        self.assertTrue(ok and (self.target / "two.txt").exists())

    def test_clone_never_overwrites(self):
        self.target.mkdir()
        ok, out = self.quiet(repos.clone, "x", self.target, str(self.origin), None)
        self.assertTrue(ok)
        self.assertIn("already exists", out)

    def test_pull_skips_uncommitted_changes(self):
        self.quiet(repos.clone, "x", self.target, str(self.origin), None)
        (self.target / "one.txt").write_text("edited")
        commit(self.origin, "two.txt")
        ok, out = self.quiet(repos.pull, "x", self.target)
        self.assertTrue(ok)
        self.assertIn("uncommitted changes", out)
        self.assertFalse((self.target / "two.txt").exists())


if __name__ == "__main__":
    unittest.main()
