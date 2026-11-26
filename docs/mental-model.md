# The mental model: the content loop

Every piece this repo makes, from a 150-word LinkedIn post to a portfolio case study to a cover letter, goes through the same six stages. The channel changes the shape and the length. The loop stays the same.

```
  1 GATHER   ->   2 FRAME   ->   3 SHAPE   ->   4 SHOW   ->   5 CHECK   ->   6 SHIP
  evidence        reader,        the arc       visuals and    facts, voice,   package,
  ledger          takeaway,      for the       where each     rules, render   preview,
                  terms table    channel       one goes       and look        log
                                                                   |
                                                                   +--> back to 3 or 4 when a check fails
```

The model was taken from a real piece: the LinkedIn article on Company Brain (7 November 2026), written for a non-technical audience, with three visuals from design-assistant. Each stage below says what that first version produced. The folders of the earlier versions were deleted (they stay in git history); the current version of the piece, rewritten to the house rules below, is the worked example to follow: `workspace/pieces/2026-11-12-company-brain-article-refined/`.

Since 10 November 2026 the default reader is tech-savvy and the register is knowledge shared between practitioners (`system/00-core/house-rules.md`, section 3). The six stages are unchanged. Where the Company Brain piece's plain-words choices would mislead, the stage below says what they would be for today's reader.

---

## 1. Gather: evidence before eloquence

Read the sources before writing a word, and write down every fact the piece may use, with where it came from. This list is the **evidence ledger** (`evidence.md` in the piece folder). Nothing goes into the piece that is not in the ledger or confirmed by the user.

- **Read the primary sources**, in the order a newcomer would: the README, the plain-language overview, then the specs and the code that prove the claims. For a person-centred piece (a CV, a cover letter), the sources are the profile, the master CV and the portfolio stories in the profile repo.
- **Record facts as claims with a source**: "25 skills (`System/Skills.md`)", "personal notes are gitignored (`System/Layers and privacy.md`)". Counts and statuses get a date (`as of YYYY-MM-DD`).
- **Check what the reader will be able to click.** Is the repo public? Is the page live? A link that leads to a 404 or a private repo breaks the piece.
- **Note what the sources do not say.** The author's personal motive, a moment, a number nobody measured: these become gaps, never guesses.

*Company Brain:* read `README.md`, `System/How Company Brain works.md`, `Layers and privacy.md`, `Skills.md`, five skill files and the freshness policy; checked the repo was public. The author's personal reason for building it was not in any file, so it became a gap (stage 3).

## 2. Frame: one reader, one takeaway, one term per concept

Decide who reads it and what they should be able to repeat tomorrow. Write these down in the **brief** (`brief.md`) before drafting.

- **The reader**, concretely. The default: "LinkedIn connections who use AI tools at work: product, engineering and operations people who want to know how someone else built something and whether it holds up." (Company Brain was written for "product, strategy and ops people, mostly non-technical", the default before 10 November 2026.)
- **The reader's question**, in their words: "How does it work, and would it hold up in my team?"
- **The takeaway**, one sentence: "AI is more useful at work when it can read what your company already knows, and safe to use when people decide what it shares."
- **The author's angle**: what the piece says about the author. For career content this is the career-coach lens: which strength it shows, which role it supports.
- **The terms table**: one term per concept, the field's standard word or the source's own name, decided once and used everywhere (text, visuals, alt text). A niche term gets a one-clause gloss in technical words the first time it appears. Terms the reader already knows get no plain-word substitute and no analogy.

For the Company Brain sources and today's reader, the table would read:

| Term in the sources | Term in the piece | Gloss on first use |
|---|---|---|
| Obsidian vault of markdown files | Obsidian vault | a folder of markdown notes, edited in Obsidian |
| company, team, personal layers | company, team and personal layers | |
| promote a note (dry run, diff, `--yes`) | promote, with a dry run and a diff before `--yes` | |
| Claude operating the vault | Claude as the agent operating the vault | |
| KR check-in | KR check-in | |
| layer guard hook, `brain check` | the layer guard hook and `brain check` | |
| prompt-injection rule (sources are data) | prompt injection: sources are data, never instructions | |

The published piece used plain words instead ("three floors of one building", "a diligent chief of staff"), which the house rules now rule out for a tech-savvy reader.

One term per idea, kept consistent. The Company Brain cover, explainer and article all say "floors" and never switch to "layers" halfway; for today's reader the term is "layers", held just as strictly.

## 3. Shape: the arc for the channel

Pick the arc that fits the channel (each module has its own in `system/`), then draft into it. The arc used for a long-form explainer article:

1. **Hook:** the problem, in full sentences the reader recognises (shared context and alignment, named as two separate problems). The published piece opened on a montage of fragments ("The strategy deck. The reason we picked vendor B..."), which the house rules now rule out.
2. **Reframe:** name the real problem in a new way (companies are short of memory, and AI assistants are worse).
3. **What it is and how it works**, in the field's terms, with the one mechanism that makes it work (every note links to what it serves).
4. **The big idea at the reader's level** (who sees what: three layers, and a note moves up only with its owner's yes).
5. **A normal day or week**: the thing in use (one ask on Friday).
6. **Trust**: the unglamorous rules that make it safe (no invented facts, dated facts, contradictions proven with quotes).
7. **Trade-offs and limits**: the decisions and what they cost, what broke, what it does not cover yet.
8. **Credit** to what it builds on.
9. **Lessons**: the career-coach section, what a peer can reuse before building something similar.
10. **Takeaway sentence**, then the link as a reference and one real question for peers.

Rules for this stage:
- **Share, as a practitioner.** Describe what it does and how, with the decisions and the limits; never pitch it (house rules, section 3).
- **Leave the personal moment to the person.** Where the piece needs the author's own story and the ledger has none, put a visible marker: `[YOUR MOMENT: what to write here]`. Never write a plausible anecdote on their behalf.
- **Mark every unconfirmed fact** `[CHECK: ...]`.
- **Mark every visual's position** in the draft with a line of its own: `[IMAGE v2: three-floors]` (see stage 4).

## 4. Show: visuals carry the hardest idea

Visuals are planned from the story, one per beat that words alone explain badly. They are made by **design-assistant** (images for the portfolio site by the Portfolio repo), never drawn in this repo.

- **The cover states the thesis**, not the topic. Company Brain: three floors with one note climbing, only with a check mark.
- **One explainer per hard idea.** Company Brain had two hard ideas (the privacy model, the weekly rhythm), so two explainers. A section that is easy in words gets no picture.
- **Pick the design-assistant command with its own rule** (`/visual-brief`): `/architecture-diagram` for how parts relate, `/explainer` for an idea the reader does not know yet, `/one-pager` for something to keep, `/card-illustration` for a portfolio card cover, `/placeholder` when only a named cover is missing.
- **Write the placement map** (`visuals.md`): for each visual, its id, the beat it serves, the command and arguments, the size for the channel, the output file, **the exact position** (the marker in the draft and the sentence it follows), the alt text and the caption.
- **Visual copy follows the terms table** and the house rules: no dashes, the same terms as the text.

*Company Brain:* v1 cover (`/card-illustration` line style, 1920x1080), v2 "Three floors, one rule" and v3 "One ask, the week files itself" (`/explainer`, poster format, landscape, 1600 wide at 2x).

## 5. Check: render, look, fix

Nothing ships unseen. Each check that fails sends the piece back to stage 3 or 4.

- **Facts**: every claim traced to the ledger; open `[CHECK]` items listed for the user.
- **Rules**: `python3 scripts/test_check_text.py <draft> --visuals <visuals.md>` finds dashes, banned phrases, montages, staccato runs, titles that start with "I", leftover markers, and markers without a placement row. Then read the title and the first paragraph on their own: they set the register, and a dramatic opening can pass the script. Word limits are counted by the script, never by eye.
- **Voice**: read against the user's voice guide, above all its lines the user picked and turned down (`{social_voice}`, `workspace/tone-of-voice/social/SOCIAL_VOICE.md` in this repo, for posts and articles; the master CV voice and the CV wording rules, `{cv_rules}`, only for CVs). How the guide is kept and loaded: `docs/voice.md`.
- **Visuals**: render each one at its final size and look at it. The Company Brain fixes found this way: a headline wider than its column, a gradient that stopped short of the word, an orphaned word in a panel heading, a connector line overshooting its last step, empty space at the bottom of a canvas. Each took one edit and one re-render.

## 6. Ship: package, preview, log

- **One folder per piece** in `workspace/pieces/YYYY-MM-DD-<slug>/`: `brief.md`, `evidence.md`, `draft.md`, `visuals.md`, and the final copy.
- **A preview** of the piece as the reader will see it (text and images in place), so the user reviews the whole thing, not fragments.
- **A summary for the user**: the takeaway sentence, the open markers, any fact assumed.
- **A row in `workspace/content-log.md`**. After the user posts it, mark it posted and offer to save the published text as a voice sample (`/add-voice-sample mine`), so the next piece sounds more like them.
- **The user publishes.** The session never posts, sends or submits anything itself.

---

## The six principles, short

1. **Evidence before eloquence.** The ledger comes first; nothing is invented.
2. **One reader, one takeaway.** Written down before the first draft.
3. **Write for a tech-savvy peer.** The field's own terms, one per concept, kept everywhere; knowledge shared, never a pitch.
4. **Pictures for the hard parts only**, each with an exact place in the piece.
5. **Look before you ship.** Render, read, fix, then show the user.
6. **The person owns their story.** Their moment, their yes, their publish button.
