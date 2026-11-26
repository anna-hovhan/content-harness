# The mental model: the content loop

Every piece this repo makes, from a 150-word LinkedIn post to a long article or a cover letter, goes through the same six stages. The channel changes the shape and the length. The loop stays the same.

```
  1 GATHER   ->   2 FRAME   ->   3 SHAPE   ->   4 SHOW   ->   5 CHECK   ->   6 SHIP
  evidence        reader,        the arc       visuals and    facts, voice,   package,
  ledger          takeaway,      for the       where each     rules, render   preview,
                  terms table    channel       one goes       and look        log
                                                                   |
                                                                   +--> back to 3 or 4 when a check fails
```

---

## 1. Gather: evidence before eloquence

Read the sources before writing a word, and write down every fact the piece may use, with where it came from. This list is the **evidence ledger** (`evidence.md` in the piece folder). Nothing goes into the piece that is not in the ledger or confirmed by the user.

- **Read the primary sources**, in the order a newcomer would: the README, the plain-language overview, then the specs and the code that prove the claims. For a person-centred piece (a CV, a cover letter), the sources are the profile, the master CV and the portfolio stories, where `config.yaml` points.
- **Record facts as claims with a source**: "25 skills (`System/Skills.md`)", "personal notes are gitignored (`System/Layers and privacy.md`)". Counts and statuses get a date (`as of YYYY-MM-DD`).
- **Check what the reader will be able to click.** Is the repo public? Is the page live? A link that leads to a 404 or a private repo breaks the piece.
- **Note what the sources do not say.** The author's personal motive, a moment, a number nobody measured: these become gaps, never guesses.

## 2. Frame: one reader, one takeaway, one term per concept

Decide who reads it and what they should be able to repeat tomorrow. Write these down in the **brief** (`brief.md`) before drafting.

- **The reader**, concretely. The default: "LinkedIn connections who use AI tools at work: product, engineering and operations people who want to know how someone else built something and whether it holds up."
- **The reader's question**, in their words: "How does it work, and would it hold up in my team?"
- **The takeaway**, one sentence: "AI is more useful at work when it can read what your company already knows, and safe to use when people decide what it shares."
- **The author's angle**: what the piece says about the author. For career content this is the career-coach lens: which strength it shows, which role it supports.
- **The terms table**: one term per concept, the field's standard word or the source's own name, decided once and used everywhere (text, visuals, alt text). A niche term gets a one-clause gloss in technical words the first time it appears. Terms the reader already knows get no plain-word substitute and no analogy.

## 3. Shape: the arc for the channel

Pick the arc that fits the channel (each module has its own in `system/`), then draft into it. The arc used for a long-form explainer article:

1. **Hook:** the problem, in full sentences the reader recognises (shared context and alignment, named as two separate problems).
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

Visuals are planned from the story, one per beat that words alone explain badly. They are made by **design-assistant**, never drawn in this repo.

- **The cover states the thesis**, not the topic.
- **One explainer per hard idea.** A section that is easy in words gets no picture.
- **Pick the design-assistant command with its own rule** (`/visual-brief`): `/architecture-diagram` for how parts relate, `/explainer` for an idea the reader does not know yet, `/one-pager` for something to keep, `/card-illustration` for a portfolio card cover, `/placeholder` when only a named cover is missing.
- **Write the placement map** (`visuals.md`): for each visual, its id, the beat it serves, the command and arguments, the size for the channel, the output file, **the exact position** (the marker in the draft and the sentence it follows), the alt text and the caption.
- **Visual copy follows the terms table** and the house rules: no dashes, the same terms as the text.

## 5. Check: render, look, fix

Nothing ships unseen. Each check that fails sends the piece back to stage 3 or 4.

- **Facts**: every claim traced to the ledger; open `[CHECK]` items listed for the user.
- **Rules**: `python3 scripts/test_check_text.py <draft> --visuals <visuals.md>` finds dashes, banned phrases, montages, staccato runs, titles that start with "I", leftover markers, and markers without a placement row. Then read the title and the first paragraph on their own: they set the register, and a dramatic opening can pass the script. Word limits are counted by the script, never by eye.
- **Voice**: read against the user's voice guide, above all its lines the user picked and turned down (`{social_voice}`, `workspace/tone-of-voice/social/SOCIAL_VOICE.md` in this repo, for posts and articles; the master CV voice and the CV wording rules, `{cv_rules}`, only for CVs). How the guide is kept and loaded: `docs/voice.md`.
- **Visuals**: render each one at its final size and look at it: a headline wider than its column, an orphaned word in a heading, a connector overshooting its shape, empty space at an edge. Each takes one edit and one re-render.

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
