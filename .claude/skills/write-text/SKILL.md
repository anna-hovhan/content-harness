---
description: Write any text that has no command of its own (a comment, a reply, a message, a bio, an about page, alt text) and check it against the house rules before showing it. Not for a LinkedIn post or article: each of those has its own command
argument-hint: "<what to write, and where it will appear>"
---

Write: $ARGUMENTS

1. Read `AGENTS.md` (session start) if it is not loaded yet.
2. If the request is one of these, say so in one line and run that workflow instead of this one: a LinkedIn post (`/write-linkedin-post`) or a LinkedIn article (`/write-linkedin-article`).
3. Run `system/50-other-text/other-text.md`. The full house rules are already loaded through `CLAUDE.md`.
4. Check the text with `printf '%s' "<text>" | python3 scripts/test_check_text.py -` (add `--max-words` and `--channel` where they apply) and fix every error before showing it.
5. Show the text as it will appear, the AI-pattern score, and any open `[CHECK]` or `[YOUR MOMENT]`.
