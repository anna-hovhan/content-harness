"""Offline tests for scripts/hooks/load_voice.py: the voice guide reaches every session.

They build a throwaway repo with its own writing-rules.yaml, so nothing here reads the user's files.
Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import load_voice  # noqa: E402

GUIDE = ("# My social voice\n\nHow I write.\n\n## How they sound\n- Conversational.\n\n"
         "## Lines I picked and lines I turned down\n- Picked: an example line.\n\n"
         "## Images\n" + "Image detail. " * 50 + "\n\n## Techniques I borrow\n- A technique.\n\n"
         "## Never in my posts\n- CV language.\n")


GUIDE_PATH = Path("workspace") / "tone-of-voice" / "social" / "SOCIAL_VOICE.md"


def make_layout(guide: str | None = GUIDE):
    """A repo with no siblings, as a worktree anywhere has: the guide is found through writing-rules.yaml."""
    tmp = tempfile.TemporaryDirectory()
    repo = Path(tmp.name) / "content"
    repo.mkdir()
    (repo / "writing-rules.yaml").write_text(
        f"schema: 1\nprovider: test\nrules:\nvoice:\n  social_voice: {GUIDE_PATH.as_posix()}\n", encoding="utf-8")
    if guide is not None:
        (repo / GUIDE_PATH).parent.mkdir(parents=True)
        (repo / GUIDE_PATH).write_text(guide, encoding="utf-8")
    return tmp, repo


class LoadVoiceTests(unittest.TestCase):
    def test_guide_is_loaded_without_the_drafting_sections(self):
        tmp, repo = make_layout()
        with tmp:
            text = load_voice.context(repo)
        self.assertIn("HR-voice-guide-first", text)
        self.assertIn("- Conversational.", text)
        self.assertIn("Picked: an example line.", text)
        self.assertIn("- CV language.", text)
        self.assertNotIn("Image detail.", text)
        self.assertNotIn("- A technique.", text)
        self.assertIn("read from the file when drafting a full post or article: Images; Techniques I borrow", text)

    def test_a_long_guide_is_cut_at_a_section_and_the_cut_is_named(self):
        long_guide = GUIDE + "\n## A long section\n" + "word " * 3000 + "\n"
        tmp, repo = make_layout(long_guide)
        with tmp:
            text = load_voice.context(repo)
        self.assertIn("before writing anything in the user's voice, even one line: A long section",
                      text.split("\n\n")[0])
        self.assertNotIn("word word", text)
        self.assertLessEqual(load_voice.size(text), load_voice.BUDGET)

    def test_a_short_section_after_a_cut_one_is_kept(self):
        head, never = GUIDE.split("## Never in my posts")
        long_guide = head + "## A long section\n" + "word " * 3000 + "\n\n## Never in my posts" + never
        tmp, repo = make_layout(long_guide)
        with tmp:
            text = load_voice.context(repo)
        self.assertNotIn("word word", text)
        self.assertIn("- CV language.", text)

    def test_the_output_stays_under_the_cap_whatever_the_guide(self):
        # The header names every section it leaves out, so it grows as the guide does: 9,000 characters of guide
        # plus a header that long went over Claude Code's cap, and past the cap Claude gets only a preview.
        path = Path("/somewhere/content-ops-harness/workspace/tone-of-voice/social/SOCIAL_VOICE.md")
        for count, fill in ((12, "word "), (40, "word "), (40, "\U0001F600 "), (400, "word ")):
            for body in (50, 400, 700, 2500):
                guide = "# Voice\n\nHow I write.\n\n" + "".join(
                    f"## Section {n}, with a heading as long as the ones a real guide has (added 2026-10-22)\n"
                    + fill * (body // len(fill)) + "\n\n" for n in range(count))
                text = load_voice.render(guide, path)
                self.assertLessEqual(load_voice.size(text), load_voice.BUDGET, (count, fill, body))
                self.assertIn("HR-voice-guide-first", text)
        self.assertLess(load_voice.BUDGET, load_voice.CAP)
        self.assertEqual(load_voice.size("\U0001F600"), 2)

    def test_a_guide_that_fits_is_loaded_whole(self):
        text = load_voice.render("# Voice\n\nHow I write.\n\n## How they sound\n- Conversational.\n", Path("guide.md"))
        self.assertTrue(text.endswith("## How they sound\n- Conversational."))
        self.assertNotIn("Read them from the file", text)
        self.assertNotIn("Left out here", text)

    def test_a_missing_guide_is_reported(self):
        tmp, repo = make_layout(guide=None)
        with tmp:
            text = load_voice.context(repo)
        self.assertIn("was not found", text)
        self.assertIn("HR-voice-guide-first", text)
        self.assertIn("writing-rules.yaml", text)  # where the path comes from
        self.assertIn("Refresh my social voice", text)  # how a guide that was never built gets built
        self.assertNotIn("worktree", text)  # the guide is in the repo, so a worktree is no longer a cause

    def test_the_guide_is_found_from_a_copy_of_the_repo_anywhere(self):
        # A worktree in another folder, with no sibling repos next to it, finds the guide all the same.
        tmp, repo = make_layout()
        with tmp, tempfile.TemporaryDirectory() as elsewhere:
            copy = Path(elsewhere) / "deep" / "worktree"
            shutil.copytree(repo, copy)
            text = load_voice.context(copy)
        self.assertIn("- Conversational.", text)
        self.assertIn(str(copy / GUIDE_PATH), text)

    def test_the_hook_prints_session_start_context(self):
        tmp, repo = make_layout()
        with tmp:
            env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
            run = subprocess.run([sys.executable, str(ROOT / "scripts" / "hooks" / "load_voice.py")],
                                 input="{}", capture_output=True, text=True, env=env, check=True)
        out = json.loads(run.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "SessionStart")
        self.assertIn("- Conversational.", out["additionalContext"])

    def test_a_guide_that_cannot_be_read_is_reported_in_the_context(self):
        tmp, repo = make_layout()
        with tmp:
            (repo / GUIDE_PATH).write_bytes(b"\xff\xfe\xfa not utf-8")
            env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
            run = subprocess.run([sys.executable, str(ROOT / "scripts" / "hooks" / "load_voice.py")],
                                 input="{}", capture_output=True, text=True, env=env)
        self.assertEqual(run.returncode, 0)
        text = json.loads(run.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("could not be loaded", text)
        self.assertIn("HR-voice-guide-first", text)

    def test_a_relative_guide_path_is_read_from_the_repo_not_the_working_folder(self):
        tmp, repo = make_layout(guide=None)
        with tmp:
            (repo / "writing-rules.yaml").unlink()  # config.yaml alone: its relative path is joined to the repo too
            (repo / "config.yaml").write_text('private:\n  social_voice: "voice/SOCIAL_VOICE.md"\n', encoding="utf-8")
            (repo / "voice").mkdir()
            (repo / "voice" / "SOCIAL_VOICE.md").write_text(GUIDE, encoding="utf-8")
            text = load_voice.context(repo)
        self.assertIn("- Conversational.", text)

    def test_an_empty_guide_is_reported(self):
        tmp, repo = make_layout(guide="\n")
        with tmp:
            text = load_voice.context(repo)
        self.assertIn("is empty", text)
        self.assertIn("HR-voice-guide-first", text)
        self.assertNotIn("loaded at session start", text)

    def test_a_doctor_that_fails_to_import_is_reported_in_the_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            hooks = Path(tmp) / "scripts" / "hooks"
            hooks.mkdir(parents=True)
            shutil.copy(ROOT / "scripts" / "hooks" / "load_voice.py", hooks)
            (hooks.parent / "doctor.py").write_text("raise RuntimeError('broken')\n", encoding="utf-8")
            env = dict(os.environ, CLAUDE_PROJECT_DIR=tmp)
            run = subprocess.run([sys.executable, str(hooks / "load_voice.py")],
                                 input="{}", capture_output=True, text=True, env=env)
        self.assertEqual(run.returncode, 0)
        text = json.loads(run.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("could not be loaded", text)
        self.assertIn("RuntimeError", text)

    def test_the_hook_is_wired_for_every_session_start(self):
        settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        groups = [g for g in settings["hooks"].get("SessionStart", [])
                  if any("load_voice.py" in h["command"] for h in g["hooks"])]
        self.assertTrue(groups, "no SessionStart hook runs load_voice.py")
        # A matcher such as "startup" would skip resume, clear and compaction, and compaction drops the guide.
        self.assertTrue(any(g.get("matcher", "") in ("", "*") for g in groups),
                        "load_voice.py runs for some SessionStart sources only")


if __name__ == "__main__":
    unittest.main()
