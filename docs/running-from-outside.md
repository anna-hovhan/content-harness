# Running this repo's skills from a session started elsewhere

A session started inside this repo loads `CLAUDE.md` and what it imports, its skills and its hooks on its own. A session started anywhere else (through a personal router skill, or a skill named `content-ops-harness:<skill>`) has none of that and does the steps below by hand. Keep this file in step with `CLAUDE.md`, the **Session start** in `AGENTS.md` and the hooks in `.claude/settings.json`: it is the one place that says what such a session does instead.

## Where to work

`$ROOT` is the clone the session found (`ROOT="$REPO"`). Work from there (`cd "$ROOT"`): the skills' paths are relative to it, and pieces go where a skill says (`workspace/pieces/...`), never into the folder the session started in.

## Start the session the repo's way

1. Read `$ROOT/CLAUDE.md`, then what it imports: `$ROOT/AGENTS.md`, `$ROOT/docs/mental-model.md` and `$ROOT/system/00-core/house-rules.md`.
2. Run the **Session start** in `AGENTS.md` from inside the repo: `config.yaml`, `python3 scripts/repos.py status`, `python3 scripts/doctor.py`, then the user's `MY_PROFILE.md` and `MY_RULES.md` from the profile repo, and their own writing rules in this repo (`{writing_overrides}`). The user's own rules win over every default, and no voice guide overrides a hard rule: the order is the house rules' opening paragraph.
3. Read the social voice guide (`social_voice` in `writing-rules.yaml`, `workspace/tone-of-voice/social/SOCIAL_VOICE.md` in this repo) in full before writing anything in the user's voice, even one line. Inside the repo a SessionStart hook loads it; from outside, this step is the only thing that does (`docs/voice.md`).
4. The sibling repos are found through `config.yaml`, by their folder names next to this repo (they may be shortcuts to the user's real clones). Never clone or pull a sibling without saying so first, as `AGENTS.md` says; never clone one that `doctor.py` finds.

Skills that write files run only when the user asks for them: if the user hasn't clearly asked for this piece of writing, confirm first.

## What the global hooks do for you

The user's skills setup wires two hooks in their global settings that run this repo's own scripts from any session. `harness_hooks.py` (since 2026-11-25) finds the checkout from the edited file or the shell command: before an edit or a shell command it runs `scripts/hooks/protect_rules.py`, which asks before a protected file changes; after a write it runs the linter (`test_check_content.py post-write`); before a `git commit` it runs the commit check; at the end of a turn it runs the Stop checks on the checkouts the session touched, pairs included. `chat_guard.py` checks the quoted text of the final reply. Where they are wired, the steps below marked *(hooked)* happen on their own; the rest are still done by hand.

## Do the hooks' work by hand

- At the start, check the harness: `echo '{}' | python3 scripts/hooks/preflight.py`. A `systemMessage` in its output names what is broken; tell the user before other work.
- Show text in the user's name in a reply as a markdown quote (`> `). The user's skills setup runs the quote check at the end of each turn: its `chat_guard.py`, a Stop hook in the user's global settings, runs this repo's `scripts/hooks/test_check_content.py chat`; where it is not wired, run the quoted text through `test_check_text.py -` yourself.
- Record each round of the user's feedback on a piece: `python3 scripts/pairs.py feedback <piece> "<their words>"`. When a piece goes to `review`, save its first version once (`python3 scripts/pairs.py snapshot <piece>`); when the user approves it (`final` or `posted`), capture its rewrite pairs (`python3 scripts/pairs.py capture <piece>`) and label each one (`pairs.py list --unlabelled`, `pairs.py label`).

- *(hooked for saved files)* Check every text before showing it: `python3 scripts/test_check_text.py <file>` for a saved file, `printf '%s' "<text>" | python3 scripts/test_check_text.py -` for chat-only text (add `--channel` and `--max-words` where they apply). Fix every error first.
- A new piece gets its row in `workspace/content-log.md`.
- *(hooked)* Ask before changing any rule file: the list is `PROTECTED` in `scripts/hooks/protect_rules.py`. By hand: a change there also updates `tests/rules.lock`.
- *(hooked)* Before a `git commit`, run the check on the content files it commits and on the commit message.

Commit and push only the way `AGENTS.md` says, and only what the user has approved. Long writing sessions still work better started inside the repo, where the prompt reminder and the voice guide load on their own: suggest it when the work grows.
