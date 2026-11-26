"""Offline tests for the two guards that close the gaps found on 2026-11-24: text shown only in chat is checked
(the quoted blocks of the final reply, read from the session transcript), and a harness that is broken says so at
session start instead of exiting 0 in silence (scripts/hooks/preflight.py).
Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import preflight  # noqa: E402
import test_check_content  # noqa: E402

BAD = "It plays a pivotal role in the team, and the agent reads every ticket the team receives."
GOOD = "The agent reads every ticket the team receives and tags each one with a product."


def event(kind, *blocks, **extra):
    content = list(blocks) if kind != "user-text" else blocks[0]
    return json.dumps({"type": "user" if kind.startswith("user") else kind,
                       "message": {"role": "user" if kind.startswith("user") else "assistant", "content": content},
                       **extra})


def text(t):
    return {"type": "text", "text": t}


def transcript(*lines):
    tmp = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    tmp.write("\n".join(lines) + "\n")
    tmp.close()
    return tmp.name


class ChatQuoteTests(unittest.TestCase):
    def test_a_bad_quote_in_the_final_reply_is_sent_back_once(self):
        path = transcript(event("user-text", "Write me a reply"),
                          event("assistant", text(f"Here it is, checked:\n\n> {BAD}\n\nPost it when ready.")))
        out = test_check_content.decide_chat({"transcript_path": path})
        self.assertEqual(out["decision"], "block")
        self.assertIn("HR-ai-no-significance-claims", out["reason"])
        self.assertIsNone(test_check_content.decide_chat({"transcript_path": path, "stop_hook_active": True}))

    def test_a_clean_quote_and_a_reply_without_quotes_pass(self):
        for body in (f"> {GOOD}", "No quote here, only a status line about the build."):
            path = transcript(event("user-text", "go"), event("assistant", text(body)))
            self.assertIsNone(test_check_content.decide_chat({"transcript_path": path}), body)

    def test_only_the_reply_after_the_last_tool_call_counts(self):
        tool = {"type": "tool_use", "id": "t1", "name": "Bash", "input": {}}
        path = transcript(event("user-text", "go"),
                          event("assistant", text(f"First draft:\n\n> {BAD}"), tool),
                          event("user", {"type": "tool_result", "tool_use_id": "t1", "content": "ok"}),
                          event("assistant", text(f"Revised:\n\n> {GOOD}")))
        self.assertIsNone(test_check_content.decide_chat({"transcript_path": path}))

    def test_text_the_harness_adds_is_not_the_users_message(self):
        path = transcript(event("user-text", "go"),
                          event("assistant", text(f"> {BAD}")),
                          event("user", text("Base directory for this skill: ..."), isMeta=True))
        self.assertEqual(test_check_content.decide_chat({"transcript_path": path})["decision"], "block")

    def test_quotes_in_code_and_short_quotes_are_skipped(self):
        self.assertEqual(test_check_content.quoted_blocks(f"```\n> {BAD}\n```\n> Two words"), [])

    def test_no_transcript_means_nothing_to_check(self):
        self.assertIsNone(test_check_content.decide_chat({}))
        self.assertIsNone(test_check_content.decide_chat({"transcript_path": "/no/such/file.jsonl"}))


class PreflightTests(unittest.TestCase):
    def test_an_old_python_fails_loudly(self):
        self.assertTrue(preflight.check_python((3, 8, 0)))
        self.assertEqual(preflight.check_python((3, 11, 4)), [])

    def test_failures_reach_the_user_and_a_pass_stays_quiet(self):
        failed = preflight.decide(["pairs.py does not load: SyntaxError"], [])
        self.assertIn("pairs.py does not load", failed["systemMessage"])
        self.assertIn("guards in this repo may be off", failed["hookSpecificOutput"]["additionalContext"])
        passed = preflight.decide([], ["AI reviewer: not calibrated"])
        self.assertNotIn("systemMessage", passed)
        self.assertIn("not calibrated", passed["hookSpecificOutput"]["additionalContext"])

    def test_the_hooks_of_this_repo_load(self):
        self.assertEqual(preflight.check_hooks(), [])

    def test_a_doctor_problem_is_a_failure(self):
        run = lambda *a, **k: SimpleNamespace(returncode=1, stdout="ok  config\nmissing  design_assistant\n", stderr="")  # noqa: E731
        self.assertIn("missing  design_assistant", preflight.check_doctor(run)[0])
        run_ok = lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr="")  # noqa: E731
        self.assertEqual(preflight.check_doctor(run_ok), [])

    def test_the_preflight_runs_first_at_session_start(self):
        hooks = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))["hooks"]["SessionStart"]
        self.assertIn("preflight.py", hooks[0]["hooks"][0]["command"])


class PreflightNeverSilentTests(unittest.TestCase):
    def test_an_unknown_reviewer_backend_is_a_note_not_a_crash(self):
        import os
        import subprocess
        env = dict(os.environ, REVIEWER_BACKEND="claude")  # a typo for claude-cli
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "hooks" / "preflight.py")], input="{}",
                             capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        context = json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("AI reviewer: status not read", context)

class SecondReviewChatTests(unittest.TestCase):
    def test_the_payloads_final_message_wins_over_the_transcript(self):
        path = transcript(event("user-text", "go"), event("assistant", text(f"> {GOOD}")))
        out = test_check_content.decide_chat({"transcript_path": path, "last_assistant_message": f"> {BAD}"})
        self.assertEqual(out["decision"], "block")

    def test_a_long_transcript_is_read_from_its_end(self):
        filler = [event("user-text", "x" * 1000) for _ in range(2500)]
        path = transcript(*filler, event("user-text", "go"), event("assistant", text(f"> {BAD}")))
        self.assertEqual(test_check_content.decide_chat({"transcript_path": path})["decision"], "block")

if __name__ == "__main__":
    unittest.main()
