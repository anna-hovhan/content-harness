# Workflow: LinkedIn article

**Trigger:** "Write a LinkedIn article about [X]" (`/write-linkedin-article`)

A long-form piece (about 1,000 to 1,600 words) that shares one thing the user built, learned or believes with tech-savvy peers: how it works, the decisions behind it and where it stops. It also shows what the piece says about the user. Run the content loop (`system/00-core/content-loop.md`); this file adds what an article needs.

**Worked example:** `workspace/pieces/2026-11-12-company-brain-article-refined/`, the Company Brain article written to the current house rules, with each idea once. Take its structure, depth and register.

## Step 0: Folder

Draft template: `system/10-linkedin-articles/templates/article.md`, copied as `draft.md`. Final copy: `article.md`.

## Step 1: Gather

Besides the sources of the topic itself, read the user's voice:
1. `{social_voice}` in full: openings, closes, length of sentences, hashtags. The user's posts in `{social_samples}` are what it is built from; read them only to refresh it (`HR-voice-guide-first`).
2. `{tone_of_voice}`, if it exists.
3. `{profile}` and `{rules}`: facts about the user and every confidentiality note.

Never take tone from cover letters, bios or the CV.

## Step 2: Frame

The default reader for an article is the tech-savvy professionals in the user's network (`system/00-core/house-rules.md`, section 3): they use AI tools, know the common terms, and read to learn how someone else built something and whether it holds up. If the user names another reader (engineers only, hiring managers in a role family, founders, a non-technical audience), write that in the brief; it changes the level of detail and the terms table.

## Step 3: Shape: the article arc

| Beat | What it does | Length |
|---|---|---|
| Title | the takeaway as a claim the article backs up, or the subject as a plain statement; never starting with "I" or "We", never a launch announcement | one line |
| Hook | the problem or question the reader has run into, stated in full sentences; no montage of fragments, no scene-setting before the point | 2 to 4 short paragraphs |
| Reframe | names the real problem in a new way | 1 to 2 paragraphs |
| What it is and how it works | the thing, its architecture or key mechanism, in the field's terms | 3 to 5 paragraphs |
| The big idea | the hardest concept, at the reader's level; usually gets an explainer or a diagram | a section |
| In use | a normal day or week with it, step by step | a section |
| Trust or proof | what makes it safe or shows it works | a short list |
| Trade-offs and limits | the decisions and what they cost, what broke, what it does not cover yet | 1 to 3 paragraphs |
| Credit | what it builds on, by name | 1 to 2 paragraphs |
| Lessons | the career-coach section: what a peer can reuse before building something similar | 3 or 4 short paragraphs |
| Takeaway | the one sentence from the brief | one line |
| Close | the link as a reference and one real question for peers; no call to adopt or try | 2 to 4 lines |

### Step 3b: Idea map and detail budget (before drafting)

Added 2026-11-13, after the user cut the Company Brain draft for repetition and for explaining trivial things.

1. **Idea map.** List every idea the piece makes (the problem, each mechanism, the thesis, each limit) and write next to it the one section where it lives. An idea with two sections loses one. The thesis may return once, as the takeaway. When the user's own text says an idea twice, "keep the ideas" means keep it once, in its best place.
2. **The ledger is a pool, not a checklist.** Use a fact only if the argument needs it. Counts, command and skill names, hook lists and step-by-step behaviour belong to the repo's README; the article keeps the decision, the reason and the trade-off.
3. **Cut the trivial.** For each paragraph ask what a practitioner would learn from it that they could not guess. Ordinary behaviour (a dry run shows a diff before writing, a feed lists connectors) gets a clause or nothing; a design decision gets its reason.
4. **Length follows the idea map**, not the 1,000 to 1,600 word range: 900 words with every idea once beats 1,400 with five repeated.

Section headings are plain statements a skimmer can follow ("Who sees what"), never questions, labels like "Introduction" or slogans like "Three floors, one rule".

Put `[YOUR MOMENT: ...]` after the hook unless the user has given their own moment. It is the line readers remember, so it is theirs to write.

## Step 4: Show

- **v1, the cover:** states the thesis, 1920x1080 at 1x. Default command: `/card-illustration` line style on a deep brand pair, with the title set as text.
- **v2 and on:** one `/explainer` (poster format, landscape, 1600 wide at 2x) per hard idea, usually the big-idea beat and the in-use beat.
- Position each in-article visual right after the sentence that sets it up, before the paragraphs that explain it, so the reader sees the picture first.

## Step 5: Check

`python3 scripts/test_check_text.py <draft.md> --visuals <visuals.md>`, then `python3 scripts/test_check_repetition.py <draft.md>` and read every warning against the idea map. No word cap; flag anything over 1,800 words to the user.

## Step 6: Ship

`article.md` holds the final text with the image markers, so the user can paste section by section and insert each image at its marker. A preview page with the text and images in place is the best review format. In LinkedIn the cover is uploaded as the article cover, not inserted in the body.
