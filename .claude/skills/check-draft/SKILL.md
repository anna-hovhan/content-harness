---
description: Check a draft against the house rules (dashes, banned phrases, the AI-pattern rules and score, word limit, open markers, image markers against the placement map)
argument-hint: '"<piece folder or draft path>" [--max-words N]'
---

Check the draft: $ARGUMENTS

1. Find the draft: a path, or `draft.md` in the named piece folder under `workspace/pieces/`.
2. Run `python3 scripts/test_check_text.py <draft> --visuals <visuals.md if the folder has one>`, adding `--max-words` from the channel (`docs/channels.md`) or the arguments. For a piece folder, also run `python3 scripts/test_check_structure.py <folder> --channel "<channel>" --status <status>` with the channel and status from `workspace/content-log.md`.
3. If the AI reviewer can run (`ANTHROPIC_API_KEY` and the `anthropic` package, or the Claude CLI, `claude`, on PATH), offer it, since every run costs money or Claude plan usage: `python3 scripts/ai_review.py <draft>`, with `--voice <social_samples>` (`python3 scripts/doctor.py --get social_samples`) for posts and articles. Report its calibration status with its findings; an uncalibrated reviewer is a second opinion, not a verdict.
4. Go through the self-check in `system/00-core/house-rules.md`, section 6, and trace each claim to the piece's `evidence.md`. The AI-pattern rules (house rules, section 2.2) run inside `test_check_text.py`: report its AI-pattern score, every error as an error, and the warnings that cost points.
5. Report errors first, then the open markers for the user. Change nothing unless the user asks.
