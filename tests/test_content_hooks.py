"""Offline tests for scripts/hooks/test_check_content.py: written content is always put through the checks.

They build a throwaway repo layout, so nothing here touches the real workspace.
Run: python3 -m unittest discover -s tests
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import test_check_content  # noqa: E402
import test_check_pieces  # noqa: E402
import protect_rules  # noqa: E402

LOG = ("| Date | Piece | Channel | Status | Folder | Published at |\n|---|---|---|---|---|---|\n"
       "| 2026-11-11 | A reply | LinkedIn post | drafting | `pieces/2026-11-11-reply/` | not yet |\n")
BAD = "It plays a pivotal role in the team.\n"
GOOD = "The vault keeps its notes in one folder.\n"


def make_repo():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    (root / "workspace" / "pieces" / "2026-11-11-reply").mkdir(parents=True)
    (root / "workspace" / "content-log.md").write_text(LOG, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    return tmp, root


def bash(command):
    return {"tool_name": "Bash", "tool_input": {"command": command}}


class ContentFileTests(unittest.TestCase):
    def test_what_counts_as_content(self):
        yes = ["workspace/pieces/x/draft.md", "workspace/pieces/x/reply.md", "workspace/pieces/x/bio.txt",
               "/elsewhere/50-applications/Acme/cover_letter_Acme.md", "/elsewhere/50-applications/Acme/cv_Acme_PM.md"]
        no = ["workspace/pieces/x/brief.md", "workspace/pieces/x/evidence.md", "workspace/pieces/x/visuals.md",
              "system/00-core/house-rules.md", "docs/guardrails.md", "scripts/test_check_text.py", "workspace/content-log.md",
              "workspace/pieces/x/preview.html", "README.md"]
        for path in yes:
            self.assertTrue(test_check_content.is_content_file(path, ROOT), path)
        for path in no:
            self.assertFalse(test_check_content.is_content_file(path, ROOT), path)


class HookDecisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp, self.root = make_repo()
        self.addCleanup(self.tmp.cleanup)
        self.piece = self.root / "workspace" / "pieces" / "2026-11-11-reply"

    def write(self, name, text, folder=None):
        path = (folder or self.piece) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_a_bad_file_is_sent_back_after_the_write(self):
        path = self.write("post.md", BAD)
        out = test_check_content.decide_post_write({"tool_input": {"file_path": str(path)}}, self.root)
        self.assertEqual(out["decision"], "block")
        self.assertIn("HR-ai-no-significance-claims", out["reason"])

    def test_a_clean_file_and_a_non_content_file_pass(self):
        self.assertIsNone(test_check_content.decide_post_write({"tool_input": {"file_path": str(self.write("post.md", GOOD))}}, self.root))
        brief = self.write("brief.md", BAD)
        self.assertIsNone(test_check_content.decide_post_write({"tool_input": {"file_path": str(brief)}}, self.root))

    def test_a_post_is_held_to_its_channel(self):
        path = self.write("post.md", "A **bold** line.\n")
        out = test_check_content.decide_post_write({"tool_input": {"file_path": str(path)}}, self.root)
        self.assertIn("HR-ai-channel-markup", out["reason"])
        words = self.write("post.md", "word " * 205 + ".\n")
        self.assertIn("over the limit of 200", test_check_content.decide_post_write({"tool_input": {"file_path": str(words)}}, self.root)["reason"])

    def test_stop_catches_files_written_through_the_shell_and_unlogged_pieces(self):
        self.write("reply.md", BAD)
        other = self.root / "workspace" / "pieces" / "2026-11-11-unlogged"
        self.write("draft.md", GOOD, other)
        out = test_check_content.decide_stop({}, self.root)
        self.assertEqual(out["decision"], "block")
        self.assertIn("HR-ai-no-significance-claims", out["reason"])
        self.assertIn("2026-11-11-unlogged/ has no row in workspace/content-log.md", out["reason"])

    def test_stop_blocks_once_and_stays_quiet_when_clean(self):
        self.write("reply.md", BAD)
        self.assertIsNone(test_check_content.decide_stop({"stop_hook_active": True}, self.root))
        self.write("reply.md", GOOD)
        self.assertIsNone(test_check_content.decide_stop({}, self.root))

    def test_commit_is_denied_for_staged_content_with_errors(self):
        path = self.write("reply.md", BAD)
        subprocess.run(["git", "add", str(path)], cwd=self.root, check=True)
        out = test_check_content.decide_commit(bash('git commit -m "Add the reply"'), self.root)
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("HR-ai-no-significance-claims", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_commit_message_notes_are_denied_and_specific_ones_pass(self):
        bad = test_check_content.decide_commit(bash('git commit -m "Refined the draft for clarity and flow"'), self.root)
        self.assertEqual(bad["hookSpecificOutput"]["permissionDecision"], "deny")
        heredoc = "git commit -F - <<'EOF'\nEnsured the piece adheres to the house rules\nEOF"
        self.assertIsNotNone(test_check_content.decide_commit(bash(heredoc), self.root))
        good = bash('git commit -m "Cut the analogy in the second paragraph\n\nCo-Authored-By: Claude <noreply@anthropic.com>"')
        self.assertIsNone(test_check_content.decide_commit(good, self.root))

    def test_commit_text_inside_another_commands_heredoc_is_not_a_commit(self):
        command = "cat > notes.txt <<'EOF'\ngit commit -m \"Refined the draft for clarity and flow\"\nEOF"
        self.assertIsNone(test_check_content.decide_commit(bash(command), self.root))

    def test_other_commands_are_ignored(self):
        for command in ["git status", "python3 scripts/test_check_text.py x.md", "git log --oneline", "echo 'git commit' > /dev/null"]:
            self.assertIsNone(test_check_content.decide_commit(bash(command), self.root), command)

    def test_the_prompt_reminder_names_the_checker_and_the_catch_all(self):
        text = test_check_content.decide_prompt({})["hookSpecificOutput"]["additionalContext"]
        for needle in ("test_check_text.py -", "/write-text", "content-log.md"):
            self.assertIn(needle, text)

    def test_a_crashing_hook_exits_zero(self):
        proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "hooks" / "test_check_content.py"), "post-write"],
                              input="{not json", capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("skipped", proc.stderr)


class VoiceLibraryTests(unittest.TestCase):
    """workspace/tone-of-voice/ keeps the user's published posts and letters exactly as written, dashes included:
    no hook ever runs the copy checks on it."""
    POST = "# Sample: a post\n# Posted: 2026-01-01\n\nIt plays a pivotal role — and the reality is, it works.\n"

    def setUp(self):
        self.tmp, self.root = make_repo()
        self.addCleanup(self.tmp.cleanup)
        self.voice = self.root / "workspace" / "tone-of-voice"
        (self.voice / "social").mkdir(parents=True)

    def test_nothing_in_the_voice_library_is_content(self):
        for name in ("social/2026-01-01-post.md", "social/SOCIAL_VOICE.md", "cover-letter-Acme.md",
                     "Cover Letter - Acme.md", "TONE_OF_VOICE.md", "social/articles/2026-01-02-article.md"):
            with self.subTest(name=name):
                self.assertFalse(test_check_content.is_content_file(self.voice / name, self.root))
                self.assertFalse(test_check_content.is_content_file(f"workspace/tone-of-voice/{name}", self.root))

    def test_the_hooks_leave_a_published_post_alone(self):
        post = self.voice / "social" / "2026-01-01-post.md"
        post.write_text(self.POST, encoding="utf-8")
        letter = self.voice / "cover-letter-Acme.md"
        letter.write_text(self.POST, encoding="utf-8")
        self.assertIsNone(test_check_content.decide_post_write({"tool_input": {"file_path": str(post)}}, self.root))
        self.assertIsNone(test_check_content.decide_post_write({"tool_input": {"file_path": str(letter)}}, self.root))
        self.assertIsNone(test_check_content.decide_stop({}, self.root))
        subprocess.run(["git", "add", str(post), str(letter)], cwd=self.root, check=True)
        self.assertIsNone(test_check_content.decide_commit(bash('git commit -m "Add a voice sample"'), self.root))


class WiringTests(unittest.TestCase):
    SETTINGS = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))["hooks"]

    def commands(self, event):
        return [h["command"] for group in self.SETTINGS.get(event, []) for h in group["hooks"]]

    def test_every_event_runs_the_content_hook(self):
        events = {"UserPromptSubmit": "prompt", "PostToolUse": "post-write", "Stop": "stop", "PreToolUse": "commit"}
        for event, mode in events.items():
            self.assertTrue(any(c.endswith(f'test_check_content.py" {mode}') for c in self.commands(event)), f"{event} {mode}")

    def test_post_write_covers_every_file_tool(self):
        group = self.SETTINGS["PostToolUse"][0]
        for tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
            self.assertIn(tool, group["matcher"])

    def test_the_new_files_are_protected_and_unlogged_pieces_fail_ci(self):
        for path in ("scripts/ai_patterns.py", "scripts/hooks/test_check_content.py", "tests/test_ai_patterns.py",
                     "tests/test_content_hooks.py"):
            out = protect_rules.decide({"tool_name": "Edit", "tool_input": {"file_path": path}, "cwd": str(ROOT)})
            self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "ask", path)
        rows = test_check_pieces.log_rows(LOG)
        with tempfile.TemporaryDirectory() as tmp:
            pieces = Path(tmp) / "pieces"
            (pieces / "2026-11-11-reply").mkdir(parents=True)
            (pieces / "2026-11-11-orphan").mkdir()
            self.assertEqual(test_check_pieces.unlogged_folders(rows, pieces), ["pieces/2026-11-11-orphan/"])


if __name__ == "__main__":
    unittest.main()
