# Workflow: portfolio blog post

**Trigger:** "Write a blog post about [X]" / "Write a post for my site's blog" / "Turn this case study into a blog post" (`/write-blog-post`)

A long-form post on the portfolio site's blog that shares one thing the user built, tried or thinks, for the reader the brief names. Run the content loop (`system/00-core/content-loop.md`); this file adds what the site's blog needs. The arc, the idea map and the detail budget are the article's: `system/10-linkedin-articles/linkedin-article.md`, steps 3 and 3b.

The blog's content is in the site's CMS (`blog_posts`), not in files. This workflow writes `article.md` and stops there. The Portfolio repo applies it the way its `AGENTS.md` says: a fresh export first, then a content script in `{portfolio_content_scripts}`. A new post starts hidden until the user sets it to Show. Never write to the database from here.

## Which piece the request is

| The user asks for | Workflow |
|---|---|
| a blog post, an article for the site | this one |
| a case study, a project page, a card for Selected work | `system/30-portfolio-pages/portfolio-page.md` (`/write-portfolio-page`) |
| a LinkedIn article | `system/10-linkedin-articles/linkedin-article.md` (`/write-linkedin-article`) |
| a LinkedIn post about a blog post or a case study | `system/20-linkedin-posts/linkedin-post.md` (`/write-linkedin-post`) |

One subject often gets both a case study and a blog post. They are two pieces with two folders. The case study shows the work (problem, decisions, proof, limits) to a reader with a minute; the post argues one point at length. They may share diagrams, and each links to the other once both are live.

## Step 0: Folder

`workspace/pieces/YYYY-MM-DD-<slug>-blog-post/`. Draft template: `system/35-blog-posts/templates/blog-post.md`, copied as `draft.md`. Final copy: `article.md`. The channel in the content log is "Portfolio blog article".

## Step 1: Gather

As for an article (`linkedin-article.md`, step 1): the topic's own sources, the voice guide (`{social_voice}`), `{profile}` and `{rules}`. Read the user's published blog articles too (`{social_samples}/articles/`): they show the length and register of this channel. If a case study on the same subject exists, read its piece folder and start the evidence ledger from its ledger.

## Step 2: Frame

The default reader is tech-savvy (`system/00-core/house-rules.md`, section 3). A blog post often has a named reader, such as leaders planning a build or peers running agents: write that reader in the brief, since it sets the terms table.

## Step 3: Shape

The article arc (`linkedin-article.md`, step 3), with the idea map and the detail budget of step 3b. What the blog changes:

| Item | Field | Rule |
|---|---|---|
| Title | `blog_posts.title`, with an optional `title_accent` | the claim or the subject; the accent is the second half of a two-part title; never starting with "I" or "We" |
| Summary | `blog_posts.summary` | one or two sentences for the blog index and link previews |
| Tags | `blog_posts.tags` | up to four |
| Length | | at most a 4-minute read on the site; the cap and how it is counted are in `{writing_overrides}`, which wins over any default here |
| Links | | markdown links in the text; every link public and live |
| Takeaway | a callout block | the one sentence from the brief |
| Close | | a link to the case study when there is one, and one real question for the reader |

No limits section: `{writing_overrides}` keeps a post's limits to a sentence or two, or none, and asks for the overarching architectural and strategic decisions in place of small details. `test_check_structure.py` does not ask a blog post for a limits heading.

## Step 4: Show

Images for the site use its own design system and the Portfolio repo's tools, never design-assistant (`system/00-core/visual-handoff.md`, Step 2).

| Visual | Made with (Portfolio repo) | Position |
|---|---|---|
| Cover | a diagram from `node scripts/design-assets.mjs diagram`, also exported as a PNG 1920 wide | `blog_posts.cover_image` (src, alt, fit, ratio) |
| In-text diagram | the same tool, as SVG | an images block after the sentence named in `visuals.md`, with alt text and a caption |

A diagram shared with a case study is made once and placed in both. Storage upload is the user's: a new file gets a new name.

## Step 5: Check

The post goes on the portfolio site: no private repo is named or described, and no repo-internal specifics appear (the dates of internal events, rule IDs, file and script names, counts, quotes from the repo). (`HR-site-private-repos`)

1. `python3 scripts/test_check_text.py <draft.md> --visuals <visuals.md>`
2. `python3 scripts/test_check_repetition.py <draft.md>`, with every warning read against the idea map.
3. `python3 scripts/test_check_structure.py <piece folder> --channel "Portfolio blog article" --status review`

Word cap: the one in `{writing_overrides}`; run step 1 with `--max-words` at that cap. `test_check_pieces.py` holds every blog post dated from 2026-11-25 to it in CI.

## Step 6: Ship

`article.md` has the final text with the image markers. Tell the user the next steps in the Portfolio repo: upload the images to Storage, take a fresh export of `blog_posts`, write the content script (the post as blocks, hidden), review it, run it, set the post to Show, then publish. Offer to do the script in the Portfolio repo as a separate task. The user publishes.
