# Post types

A post type is a blueprint for one kind of LinkedIn post that comes up again and again and goes wrong in known ways. Leaving a job is the first. The workflow (`system/20-linkedin-posts/linkedin-post.md`) runs as usual; the type replaces its standard arc (Hook, The detail, What it means, Close) with the type's own lines, and adds the steps where a wrong move would cost the user something. A type is part of `/write-linkedin-post`, never a skill of its own, so a LinkedIn post still has one path.

## When the workflow uses one

At Step 0 the workflow lists the files in this folder (every `.md` file but this README) and reads the "Use it when" line of each:

- When one matches the idea, the workflow follows that file from Step 1 on.
- When the user names a type (`/write-linkedin-post leaving a job: <idea>`, or "a post about leaving my job"), it uses that one.
- When two match, it asks the user which, in the same batch as its other questions.
- When none matches, the post takes the standard arc.

When it shows the draft, it says which type it used, or that it used none, so the user can switch.

## What every type file has

Every type file has these, in this order, and `tests/test_post_types.py` checks them:

1. A title: `# Post type: <name>`.
2. Five lines under the title. `**Goal:**` says what the post is for: who reads it and what they come away with. Every choice in the type follows from it. `**Use it when:**` says which ideas the type fits, and it is what the workflow matches. `**Not for:**` names the near misses. `**Word cap:**` gives the limit, hook to close. `**Template:**` names the draft template: its own in `../templates/`, or the standard `post.md`.
3. `## Source`: where the method comes from, credited once by name with the date it was read, and what that source says. What the user set for the type is named here too, with its date. A type this repo wrote itself says so here.
4. `## Before drafting`: what to settle with the user before the first draft.
5. `## Gather`: where each fact comes from (`{profile}`, `{cv_master}`, `{portfolio_stories}`, `{rules}`).
6. `## Shape`: the type's lines, as a table, in place of the arc in Step 3.
7. `## What stays out`.
8. `## Image`: only what this kind of post adds to Step 4.
9. `## Check`: the exact commands, with the type's word cap, and a self-check for what the scripts cannot see.
10. `## After it is live`: what changes elsewhere once the post is up, and which repo owns it.

A heading may go on after a colon (`## Shape: the four lines`), and a type may add sections of its own between these. Every `##` and `###` section opens with a line saying where it comes from: *From the source*, *From the user*, *This repo*, or a mix of them, so the user can see at a glance what the source said, what the user set and what this repo added.

## Where a type's rules sit

From the first, which wins, down:

1. The user's own rules: `{writing_overrides}` for writing, and `MY_RULES.md` (`{rules}`) for confidentiality.
2. The user's voice guide (`{social_voice}`), the post rules (`{social_voice_rules}`) and the house rules (`system/00-core/house-rules.md`), in the order they set among themselves.
3. The post type.
4. `linkedin-post.md`.

So a type adds to the rules above it and never relaxes them, with two exceptions.

**Length.** A type may set a word cap below the workflow's 200 and, for its own posts only, have no minimum. The post rules give 120 to 250 words as a default in their section 3 (their hard rules are sections 1 and 2), and a minimum in the user's voice guide gives way to the type in the same way. A lower cap in the user's own writing rules (`{writing_overrides}`) or in the voice guide still applies, and a minimum in `{writing_overrides}` wins over the type; the session then says so when it shows the draft. A type that uses this exception says so in its `**Word cap:**` line.

**What the user set for the type.** When the user says how one kind of post is to be written, that is the user's own rule for it. For that type's posts it holds where it differs from the voice guide, the post rules or the style and voice rules of the house rules (sections 2 to 4). The type marks each such rule *From the user* and lists every rule it sets aside in a `## Where it differs` section, as a table: the rule above, what the type does, and who set it. A rule that is not in that table holds in full. Three things never give way: section 1 of the house rules (truth, unknowns, confidentiality), every error `scripts/test_check_text.py` reports, and the user's own rules (`{writing_overrides}`, `MY_RULES.md`). When the session shows a draft, it names each row of the table the post uses, so the user can still say no.

## Adding a type

1. Write `<type>.md` in this folder (lowercase, with hyphens, such as `leaving-a-job.md`) with the sections above. Credit the source once, and keep its points apart from what the user set and from this repo's additions.
2. If the type needs fields of its own in the draft, add `../templates/post-<type>.md` with the sections of `post.md` (`**Status:**`, `## Post`, `## Other hooks to try`, `## Check before posting`), so the checkers count and read it the same way. Otherwise point `**Template:**` at `post.md`.
3. Run `python3 scripts/test_check_text.py system/20-linkedin-posts/post-types/<type>.md` and fix every error, then `python3 -m unittest discover -s tests`.

Nothing else has to change: the workflow finds the file by listing this folder, and the tests read every file in it. The docs name leaving a job only as an example.
