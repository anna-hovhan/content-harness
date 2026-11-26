# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

- @AGENTS.md
- @docs/mental-model.md
- @system/00-core/house-rules.md

`AGENTS.md` holds the behaviour rules, the session start and the command table. `docs/mental-model.md` is the content loop every module runs. `house-rules.md` is imported too, so the full writing rules are in every session, whatever is being written. This file covers what they don't: commands, scripts and architecture.

## Commands

```bash
python3 scripts/doctor.py                                   # are the sibling repos, private files and writing rules where config.yaml and writing-rules.yaml say? do rule copies name their HR- IDs?
python3 scripts/test_rule_sync.py <file>                         # does a file that restates house rules name each rule's ID?
python3 scripts/repos.py status                             # siblings: present, branch, uncommitted changes, behind their remote
python3 scripts/repos.py sync                               # clone missing siblings from their git URLs, fast-forward the rest
python3 scripts/test_check_text.py <draft.md>                    # dashes, banned phrases, the AI-pattern rules and score, open markers
printf '%s' "<text>" | python3 scripts/test_check_text.py -      # any text, no file needed (add --channel 'LinkedIn post')
python3 scripts/test_check_text.py <draft.md> --max-words 200    # also a word limit (posts)
python3 scripts/test_check_text.py <draft.md> --visuals <visuals.md>   # image markers vs the placement map
python3 scripts/test_check_pieces.py                             # the house rules and the loop structure on every piece in review, final or posted (CI runs it)
python3 scripts/test_check_structure.py <piece folder>           # did the piece go through the loop: brief, ledger, traced numbers and links, limits, status
python3 scripts/ai_review.py <draft.md> [--voice <dir>]     # AI reviewer against system/00-core/test_review-rubric.md (API key, or the Claude CLI: REVIEWER_BACKEND)
python3 scripts/test_calibrate_reviewer.py [--dry-run] [--jobs 4]  # calibrate it on the user's cases and rewrite pairs; rerun after any model or rubric change
python3 scripts/test_calibrate_reviewer.py --set synthetic       # the smoke test on made-up pairs, never a calibration
python3 scripts/pairs.py feedback <piece> "<words>"             # one round of the user's feedback on a piece
python3 scripts/pairs.py list --unlabelled                       # rewrite pairs captured at approval that wait for a label
python3 scripts/pairs.py label <id> --criterion <id> | --any | --skip "<why>"
echo '{}' | python3 scripts/hooks/preflight.py              # the session-start check that the harness works
python3 -m unittest discover -s tests                       # offline tests, incl. the rules lock and feedback cases; CI runs them on every PR
```

Rendering a visual happens in design-assistant: its commands are in its `.claude/commands/`, its generators run with `npm run design -- <generator> ...` there. Write outputs into the piece folder's `visuals/` or into design-assistant's `out/`, and record the path in `visuals.md`.

## Architecture

- **`system/00-core/`** is shared by every module: `content-loop.md` (the stages as steps), `house-rules.md` (writing rules; section 2.2 holds the AI writing patterns, checked by `ai_patterns.py` and scored), `banned-phrases.txt` (enforced by `test_check_text.py`), `social-voice-rules.md` (the rules for social posts), `voice-library.md` (how the voice samples are kept and the social voice guide is built, run by `/add-voice-sample`), `visual-handoff.md` (how to plan visuals, pick the repo that makes each one and place images), and `templates/` (the brief, the evidence ledger, the placement map and the guide's template). `system/40-job-applications/` also holds the wording rules for a CV, a cover letter and an outreach message. Sizes and limits per channel are in `docs/channels.md`.
- **Each module** (`10-` to `50-`) has one workflow file and its templates. A workflow names the arc for its channel and anything the channel adds to the loop; it never repeats the core rules. The posts module also has `post-types/`: one blueprint per kind of post, which `linkedin-post.md` finds by listing the folder and uses in place of its standard arc.
- **Skills** in `.claude/skills/<name>/SKILL.md` find or create the piece folder and run the workflow. Skills that write files carry `disable-model-invocation: true`; `/content-status` and `/check-draft` are read-only.
- **`config.yaml`** is the only place paths and git URLs of other repos are written (`repos:` and `git:`); `scripts/repos.py` clones and updates them from it. Workflows refer to `{design_assistant}`, `{profile}` and so on, resolved from it.
- **`writing-rules.yaml`** is the writing rules contract: every writing rule and voice file this repo owns, by key (`{house_rules}`, `{cv_rules}`, `{social_voice}`, `{writing_overrides}` and the rest). `scripts/doctor.py` resolves its keys with those of `config.yaml`, and a repo that consumes the rules reads them through it. How it works and how a rule change reaches each repo: `docs/writing-rules-contract.md`.
- **Scripts** are standard-library Python, so they run anywhere with `python3`.
- **The user's voice** is described in one file, the social voice guide in this repo (`workspace/tone-of-voice/social/SOCIAL_VOICE.md`), which a SessionStart hook (`scripts/hooks/load_voice.py`) loads into every session; `/add-voice-sample` keeps the posts it is built from. How it is kept, loaded and checked: `docs/voice.md`.
- **Guardrails against drift.** CI (`checks.yml`) runs the tests and `test_check_pieces.py` on every pull request; the rules lock, the protected-files hook, the structure check, the HR- rule IDs and the AI reviewer keep the rules and the quality from drifting. What each one does, when it runs and how to change a rule on purpose: `docs/guardrails.md`.

## Adding a module

1. `system/<NN>-<name>/<name>.md` with its arc and what it adds to the loop, plus `templates/`.
2. `.claude/skills/<command>/SKILL.md`.
3. A row in the command tables in `AGENTS.md` and `README.md`, and the channel's sizes and limits in `docs/channels.md`.
