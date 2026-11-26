# Workflow: the content loop

Every module runs these steps. The module's own workflow says which arc to use and what its channel adds; this file says what every piece does. The reasoning behind each step is in `docs/mental-model.md`.

## Step 0: Open the piece folder

1. Run `python3 scripts/doctor.py` if it has not run this session.
2. Create `workspace/pieces/YYYY-MM-DD-<slug>/` (today's date, a short slug for the topic and channel, such as `company-brain-linkedin-article`). If a folder for the same piece exists, continue in it.
3. Copy into it from `system/00-core/templates/`: `brief.md`, `evidence.md`, `visuals.md`. Copy the module's own draft template as `draft.md`. Never edit the templates themselves.
4. Add a row to `workspace/content-log.md` with status `drafting`.

## Step 1: Gather (evidence ledger)

1. List the sources: what the user named, the idea file, the repo or project the piece is about, and the user's own files (`{profile}`, `{rules}`, `{cv_master}`, `{portfolio_stories}`).
2. Read them in the order a newcomer would: overview first, then the specifics that prove each claim.
3. Write every usable fact into `evidence.md` as a claim with its source file (and a date for anything that changes: counts, statuses, versions).
4. Check every link the piece may use: is the repo public, is the page live? Record the answer.
5. Write down the gaps: what the piece needs that no source says. Personal motives and moments are always gaps until the user supplies them.

## Step 2: Frame (brief)

Fill `brief.md`: channel, reader, the reader's question, the one-sentence takeaway, the author's angle, the arc, and the terms table (one term per concept, the field's own word, with a one-clause gloss for niche terms only). The default reader is tech-savvy (`system/00-core/house-rules.md`, section 3). If the reader or the channel is unclear and changes the level of detail, ask the user once, in one batch, before drafting.

## Step 3: Shape (draft)

1. Draft into the module's arc, in `draft.md`.
2. Use the terms table's words everywhere.
3. Write as a practitioner sharing knowledge with peers (house rules, section 3): how it works, the decisions and their reasons, the trade-offs and limits. Describe; never pitch.
4. Draft inside the AI-writing-pattern rules (`system/00-core/house-rules.md`, section 2.2): specific facts, plain "is" and "has", no unasked contrasts, no chatbot talk, no stock headings.
5. Put `[YOUR MOMENT: ...]` where the user's own story belongs and the ledger has none, and `[CHECK: ...]` on any fact not yet confirmed.
6. Put an image marker on its own line where each visual will sit: `[IMAGE v2: three-floors]`. The cover of an article or the image of a post is `v1`.

## Step 4: Show (visual plan and visuals)

Follow `system/00-core/visual-handoff.md`: fill `visuals.md`, make each visual in design-assistant, render it at its final size and look at it.

## Step 5: Check

1. `python3 scripts/test_check_text.py workspace/pieces/<piece>/draft.md --visuals workspace/pieces/<piece>/visuals.md`, plus `--max-words N` when the channel has a limit. Fix every error.
2. Go through the self-check in `system/00-core/house-rules.md`, section 6, then read the draft once for what the AI-pattern checks cannot see (a generic claim where a fact belongs, a contrast nobody asked for, a topic defined as a proper noun). `test_check_text.py` prints an AI-pattern score; 85 or more passes, and a lower score is fixed, not argued with. Saved files are also checked by the hooks in `.claude/settings.json`.
3. Read the title and the first paragraph on their own, against the user's voice guide (`{social_voice}` for posts and articles): they set the register for everything after them. A montage, a staccato run, a dramatic flourish or a title that starts with "I" sends the piece back to Step 3 (Shape), even when the script passes.
4. Trace every claim in the draft to `evidence.md`. Anything without a source becomes `[CHECK: ...]` or comes out.
5. Look at every rendered visual at final size. Fix overflow, clipping, orphaned words and anything that contradicts the text, then render again.

A failed check sends the piece back to step 3 or 4.

## Step 6: Ship

1. Write the final copy as the module says (for example `article.md`, `post.md`, `page.md`).
2. Show the user the piece as it will appear: text and images in place. Where the session can publish a private preview page, do so.
3. Tell the user, in a few lines: the takeaway sentence, every open `[YOUR MOMENT]` and `[CHECK]` marker, and any fact assumed.
4. Set the status in `brief.md` and `workspace/content-log.md` to `review`, then `final` when the user approves.
5. When the user says it is live, set `posted` and offer to save the published text as a voice sample (`/add-voice-sample mine`).

The user publishes. Never post, send or submit anything yourself.
