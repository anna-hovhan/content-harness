#!/usr/bin/env python3
"""Claude Code hook: every piece of written content goes through the house-rule checks, whatever its type.

Wired in .claude/settings.json, one mode per event (argv[1]):

  prompt      UserPromptSubmit: remind the session, on every prompt, that anything written in the user's name is
              checked before it is shown, and how (scripts/test_check_text.py, also on standard input).
  post-write  PostToolUse on Edit, Write, MultiEdit and NotebookEdit: when the file is content (a draft, an article, a
              post, a page, a cover letter, a CV, any file in a piece folder), check it and send the errors back.
  stop        Stop: before the session ends its turn, check every content file changed in the working tree (this catches
              files written through the shell) and that its piece folder is in workspace/content-log.md; check the text
              the reply shows as a quote (chat-only text in the user's name, see `chat`); save the first version of a
              piece the user is about to read and capture the rewrite pairs of a piece the user approved
              (scripts/pairs.py), asking the session to label new pairs. Blocks once.
  chat        Stop, for sessions started outside this repo: only the check of the
              text the last reply shows as a quote. A reply shows text in the user's name as a markdown quote ("> "), so
              chat-only text, which no file hook sees, is checked too. Blocks once.
  commit      PreToolUse on Bash: before a `git commit`, check the content files it commits and the commit message
              (HR-ai-specific-change-notes, HR-ai-no-service-register). Denies on errors.

Content files: .md and .txt files under workspace/pieces/ (except brief, evidence, visuals, feedback and the .first/
snapshot of a piece's first version), and cv_*, cover* files
anywhere (a CV or cover letter folder). Rule files, docs, templates and scripts are not content,
and neither is anything under workspace/tone-of-voice/: the user's voice library keeps their published posts, letters and
bios exactly as they wrote them, dashes included, so the copy checks never run on it.
Errors come from scripts/test_check_text.py (the whole house-rule check, the AI-pattern rules and the score), the piece's
visual map and word limit, and, for a piece the log marks review, final or posted, scripts/test_check_structure.py.

A hook that crashes must not stop a session: any exception is reported on stderr and the hook exits 0.
Chat-only text is not a file: the stop and chat modes read it from the session transcript, as the quoted blocks of
the last reply.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import ai_patterns  # noqa: E402
import pairs  # noqa: E402
import test_check_pieces  # noqa: E402
import test_check_text  # noqa: E402

PIECES = ROOT / "workspace" / "pieces"
VOICE_LIBRARY = ("workspace", "tone-of-voice")  # the user's own writing, kept exactly as written: never checked
NOT_COPY = {"brief.md", "evidence.md", "visuals.md", "readme.md", "content-log.md", "feedback-log.md", "feedback.md",
            "meta.json"}
COPY_NAME = re.compile(r"^(?:cv|cover)[-_ ]|cover[-_ ]?letter", re.I)
MAX_LINES = 12
QUOTE_MIN_WORDS = 8  # a shorter quote is a name or a phrase, not text in the user's name
TAIL_BYTES = 2_000_000  # how much of the transcript's end the chat check reads

REMINDER = (
    "House rules (system/00-core/house-rules.md, loaded through CLAUDE.md) apply to anything written in the user's name, "
    "whatever its type or length: a post, a comment, a reply, a message, a bio, a CV line, image text, alt text. "
    "Before showing text meant to be posted, sent or submitted, run it through the checker and fix every error: "
    "printf '%s' \"<text>\" | python3 scripts/test_check_text.py - [--channel 'LinkedIn post'] [--max-words N]. "
    "Text worth keeping goes in workspace/pieces/<date>-<slug>/ with a row in workspace/content-log.md; hooks check saved files. "
    "Show text in the user's name in a reply as a markdown quote (> ), so the stop hook checks it too. "
    "Record each round of the user's feedback on a piece: python3 scripts/pairs.py feedback <piece> \"<their words>\". "
    "For a request that is not one of the channel commands, use /write-text. Facts come from the evidence, never from invention."
)


def is_content_file(path: str | Path, root: Path = ROOT) -> bool:
    p = Path(path)
    if not p.is_absolute():
        p = root / p
    if p.suffix.lower() not in (".md", ".txt") or p.name.lower() in NOT_COPY or pairs.FIRST_DIR in p.parts:
        return False
    try:
        p.resolve().relative_to(root.joinpath(*VOICE_LIBRARY).resolve())
        return False
    except ValueError:
        pass
    try:
        p.resolve().relative_to((root / "workspace" / "pieces").resolve())
        return True
    except ValueError:
        return bool(COPY_NAME.search(p.name))


def piece_row(path: Path, root: Path = ROOT) -> dict | None:
    """The content-log row whose folder holds this file."""
    log = root / "workspace" / "content-log.md"
    if not log.exists():
        return None
    for row in test_check_pieces.log_rows(log.read_text(encoding="utf-8")):
        folder = (root / "workspace" / row["folder"]).resolve()
        try:
            path.resolve().relative_to(folder)
            return row
        except ValueError:
            continue
    return None


def check_file(path: str | Path, root: Path = ROOT) -> dict:
    """{errors, warnings, score} for one content file, with its piece's channel, word limit, visual map and structure."""
    p = Path(path)
    if not p.is_absolute():
        p = root / p
    text = p.read_text(encoding="utf-8")
    row = piece_row(p, root)
    channel = row["channel"] if row else None
    is_copy = p.name in test_check_pieces.FINAL_COPY + ("draft.md",)
    visuals = p.parent / "visuals.md"
    max_words = test_check_pieces.POST_WORD_LIMIT if channel and "post" in channel.lower() and is_copy else None
    result = test_check_text.check(text, max_words, visuals.read_text(encoding="utf-8") if visuals.exists() and is_copy else None,
                              channel=channel)
    errors, warnings = list(result["errors"]), list(result["warnings"])
    if row and row["status"] in test_check_pieces.CHECKED and is_copy:
        import test_check_structure
        structure = test_check_structure.check_folder(p.parent, row["channel"], row["status"])
        errors += structure["errors"]
        warnings += structure["warnings"]
    return {"errors": errors, "warnings": warnings, "score": result["score"]}


def changed_files(root: Path = ROOT) -> list[Path]:
    """Modified, added and untracked files in the working tree."""
    out = subprocess.run(["git", "status", "--porcelain", "-uall"], cwd=root, capture_output=True, text=True).stdout
    files = []
    for line in out.splitlines():
        name = line[3:].split(" -> ")[-1].strip().strip('"')
        if name:
            files.append(root / name)
    return files


def unlogged_pieces(files: list[Path], root: Path = ROOT) -> list[str]:
    seen, out = set(), []
    for f in files:
        if piece_row(f, root) is None:
            try:
                folder = f.resolve().relative_to((root / "workspace" / "pieces").resolve()).parts[0]
            except (ValueError, IndexError):
                continue  # a cv or cover letter outside this repo has no piece folder
            if folder not in seen:
                seen.add(folder)
                out.append(folder)
    return out


def report(results: dict[str, dict], unlogged: list[str]) -> str | None:
    """The text sent back to the session, or None when every file is clean."""
    lines = []
    for name, r in results.items():
        if r["errors"]:
            lines.append(f"{name} (AI-pattern score {r['score']['score']}/100):")
            lines += [f"  {e}" for e in r["errors"][:MAX_LINES]]
            if len(r["errors"]) > MAX_LINES:
                lines.append(f"  ...and {len(r['errors']) - MAX_LINES} more; run python3 scripts/test_check_text.py {name}")
    for folder in unlogged:
        lines.append(f"workspace/pieces/{folder}/ has no row in workspace/content-log.md: add one (status drafting), "
                     "so test_check_pieces.py checks it in CI.")
    if not lines:
        return None
    return ("The house-rule checks failed. Fix the text itself (do not weaken a rule or a check), then re-save it. "
            "Warnings are not listed; run scripts/test_check_text.py to read them.\n" + "\n".join(lines))


def decide_post_write(payload: dict, root: Path = ROOT) -> dict | None:
    tool_input = payload.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not path or not is_content_file(path, root) or not Path(path if Path(path).is_absolute() else root / path).exists():
        return None
    name = str(path)
    message = report({name: check_file(path, root)}, [])
    if not message:
        return None
    return {"decision": "block", "reason": message,
            "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": message}}


def last_reply(transcript_path: str | None) -> str:
    """The final reply of the turn: the assistant's text after its last tool call, from the session transcript (JSONL).
    Text shown earlier in the turn, before a tool call, was a step on the way and is not checked."""
    if not transcript_path or not Path(transcript_path).exists():
        return ""
    texts = []
    with open(transcript_path, "rb") as fh:  # the last events are enough: read the tail, not a long session's whole file
        fh.seek(0, 2)
        size = fh.tell()
        fh.seek(max(0, size - TAIL_BYTES))
        tail = fh.read().decode("utf-8", errors="replace")
    lines = tail.splitlines()[1:] if size > TAIL_BYTES else tail.splitlines()
    for line in reversed(lines):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        content = (event.get("message") or {}).get("content")
        if event.get("type") == "user":
            if event.get("isMeta"):
                continue  # text the harness adds (a loaded skill, a reminder), not the user and not a tool result
            break  # a tool result or the user's own message: the final reply starts after it
        if event.get("type") != "assistant" or not isinstance(content, list):
            continue
        blocks = [b for b in content if isinstance(b, dict)]
        tool_at = max((i for i, b in enumerate(blocks) if b.get("type") == "tool_use"), default=-1)
        texts += [b.get("text", "") for b in reversed(blocks[tool_at + 1:]) if b.get("type") == "text"]
        if tool_at >= 0:
            break
    return "\n\n".join(reversed(texts))


def quoted_blocks(text: str) -> list[str]:
    """Markdown quotes ("> ...") outside code fences, of QUOTE_MIN_WORDS words or more."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    blocks, current = [], []
    for line in text.splitlines() + [""]:
        if line.lstrip().startswith(">"):
            current.append(re.sub(r"^\s*>\s?", "", line))
        elif current:
            block = "\n".join(current).strip()
            if len(block.split()) >= QUOTE_MIN_WORDS:
                blocks.append(block)
            current = []
    return blocks


def chat_report(payload: dict) -> str | None:
    """Errors in the text the last reply shows as a quote, or None."""
    lines = []
    # The Stop payload's own copy of the final message, where Claude Code sends one, is the reply for sure; the
    # transcript is the fallback, read from its end.
    final = payload.get("last_assistant_message")
    reply = final if isinstance(final, str) and final.strip() else last_reply(payload.get("transcript_path"))
    for i, block in enumerate(quoted_blocks(reply), 1):
        result = test_check_text.check(block, None, None, channel=None)
        if result["errors"]:
            head = " ".join(block.split()[:8])
            lines.append(f"quote {i} (\"{head}...\", AI-pattern score {result['score']['score']}/100):")
            lines += [f"  {e}" for e in result["errors"][:MAX_LINES]]
    if not lines:
        return None
    return ("Text your reply shows as a quote breaks the house rules. If it is text in the user's name, fix it and show it "
            "again; if it quotes something else (a rule, a line the user turned down), say so in one line and leave it.\n"
            + "\n".join(lines))


def pair_report(captured: dict[str, int], root: Path = ROOT) -> str | None:
    new = {k: v for k, v in captured.items() if v}
    if not new:
        return None
    names = ", ".join(f"{n} from {k}" for k, n in new.items())
    return (f"The user approved a piece, so its rewrite pairs were captured ({names}) in tests/feedback/pairs.json. "
            "Label each from its feedback and the rubric (system/00-core/test_review-rubric.md): "
            "python3 scripts/pairs.py list --unlabelled, then python3 scripts/pairs.py label <id> --criterion <id> "
            "(the criterion the first version broke), --any (the user's taste, no criterion names it) or "
            "--skip \"<why>\" (a fact or content change a reviewer cannot judge).")


def decide_stop(payload: dict, root: Path = ROOT) -> dict | None:
    # The first version and the rewrite pairs are kept whatever else this turn needs (pairs.py).
    captured = {}
    try:
        # The text checks only: the snapshot is the text the user reads, whatever the folder's structure.
        # On the turn's second Stop the user is about to read the text whatever it says: save it then.
        clean = None if payload.get("stop_hook_active") else (
            lambda f: not test_check_text.check(f.read_text(encoding="utf-8"))["errors"])
        pairs.snapshot_ready(root, is_clean=clean)
        captured = pairs.capture_ready(root)
    except Exception as exc:  # the pairs must not stop the content checks
        print(f"test_check_content.py stop: pairs skipped, {type(exc).__name__}: {exc}", file=sys.stderr)
    if payload.get("stop_hook_active"):
        # Already sent back once this turn: let the session end, unless pairs were captured just now. A piece is
        # captured once, so this asks at most once more, and the request to label them is not lost.
        message = pair_report(captured, root)
        return {"decision": "block", "reason": message} if message else None
    parts = []
    files = [f for f in changed_files(root) if f.exists() and is_content_file(f, root)]
    if files:
        results = {str(f.relative_to(root)): check_file(f, root) for f in files}
        parts.append(report(results, unlogged_pieces(files, root)))
    parts += [chat_report(payload), pair_report(captured, root)]
    message = "\n\n".join(p for p in parts if p)
    return {"decision": "block", "reason": message} if message else None


def decide_chat(payload: dict, root: Path = ROOT) -> dict | None:
    if payload.get("stop_hook_active"):
        return None
    message = chat_report(payload)
    return {"decision": "block", "reason": message} if message else None


def staged_files(command: str, root: Path = ROOT) -> list[Path]:
    names = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=root, capture_output=True, text=True).stdout.split("\n")
    if re.search(r"\bgit\s+(?:-\S+\s+)*commit\b[^|;&]*\s-\w*a|--all\b", command):
        names += subprocess.run(["git", "diff", "--name-only"], cwd=root, capture_output=True, text=True).stdout.split("\n")
    return [root / n for n in dict.fromkeys(n for n in names if n)]


COMMIT = re.compile(r"(?:^|[;&|(]\s*)(?:\w+=\S+\s+)*git\s+(?:-\S+\s+\S+\s+|-\S+\s+)*commit\b")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")


def commit_statements(command: str) -> list[str]:
    """The text of each real `git commit` in a shell command: its line, plus the heredoc that carries its message.
    Text inside the heredoc of another command (a file being written, a test) is not a commit."""
    found, lines, i = [], command.splitlines(), 0
    while i < len(lines):
        line, body = lines[i], []
        m = HEREDOC.search(line)
        if m:
            end = i + 1
            while end < len(lines) and lines[end].strip() != m.group(2):
                body.append(lines[end])
                end += 1
            i = end
        if COMMIT.search(line):
            found.append("\n".join([line] + body))
        i += 1
    return found


def decide_commit(payload: dict, root: Path = ROOT) -> dict | None:
    if payload.get("tool_name") != "Bash":
        return None
    command = (payload.get("tool_input") or {}).get("command", "")
    commits = commit_statements(command)
    if not commits:
        return None
    # The message is what the commit statements carry; the attribution trailers are ordinary text and never match.
    note_hits = ai_patterns.commit_message_hits("\n".join(commits))
    files = [f for f in staged_files("\n".join(commits), root) if f.exists() and is_content_file(f, root)]
    message = report({str(f.relative_to(root)): check_file(f, root) for f in files}, []) or ""
    if note_hits:
        message += ("\nThe commit message breaks the change-note rules: "
                    + "; ".join(h["message"] for h in note_hits[:5]) + ". Say what changed, specifically.")
    if not message.strip():
        return None
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": message.strip()}}


def decide_prompt(payload: dict) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": REMINDER}}


def main(argv: list[str] | None = None) -> int:
    mode = (sys.argv[1:] if argv is None else argv)[:1]
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        handler = {"prompt": decide_prompt, "post-write": decide_post_write, "stop": decide_stop,
                   "commit": decide_commit, "chat": decide_chat}.get(mode[0] if mode else "")
        out = handler(payload) if handler else None
        if out:
            print(json.dumps(out))
    except Exception as exc:  # a broken guard must not break the session; say so where the user can see it
        print(f"test_check_content.py {' '.join(mode)}: skipped, {type(exc).__name__}: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
