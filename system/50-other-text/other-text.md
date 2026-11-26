# Workflow: other text

**Trigger:** "Write [anything else]": a comment, a reply, a message, a bio, an about page, alt text, a recommendation, any text that is not a LinkedIn article or a LinkedIn post (`/write-text`)

The same loop in its short form, for text the other modules do not cover. A request for a LinkedIn post or article goes to its own workflow (`AGENTS.md`, Commands and triggers), even when this command was typed. The house rules (`system/00-core/house-rules.md`) apply in full, the AI-writing-pattern rules in section 2.2 included, and the user's own writing rules (`{writing_overrides}`) win over them, as the house rules' opening paragraph sets out. Nothing about the length of the text lowers the bar.

## Step 1: Gather and frame

1. Ask, in one batch, only what the request leaves open: where the text will appear (platform, and its limit), who reads it, and what it should do for that reader.
2. Read `{profile}` and `{rules}` for facts and confidentiality. Every fact in the text comes from there, from a source the user names, or from the user. A fact that is missing becomes `[CHECK: ...]`; a personal moment becomes `[YOUR MOMENT: ...]`.
3. For a reply or comment, read what it answers first. For text in the user's voice, draft from `{social_voice}`, which the session start loads; without it in context, read the file before the first draft. A line meant for a post or an article is in the user's social voice too (`HR-voice-guide-first`).

## Step 2: Draft and check

1. Draft the text. One point; the field's own terms; no pitch.
2. Check it before showing it, from standard input if it is not saved:
   `printf '%s' "<text>" | python3 scripts/test_check_text.py - --max-words N [--channel 'LinkedIn post']`
   Fix every error in the text itself, then check again. Read the AI-pattern score (85 or more passes) and every warning.
3. Go through the self-check in `house-rules.md`, section 6.

## Step 3: Show

Show the text exactly as it will appear, as a markdown quote (`> `) so the Stop hook checks it once more, with the score line from the checker, the open markers and any fact assumed. If the user wants to keep it, save it as `workspace/pieces/YYYY-MM-DD-<slug>/draft.md` (final copy `text.md`), add a row to `workspace/content-log.md` (channel "Other text") and fill `brief.md` and `evidence.md` from the templates when the status goes to `review`. A text that is only for now needs no folder.

The user sends or posts it. Never send, post or submit anything yourself.
