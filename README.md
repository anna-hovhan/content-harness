# Content harness

A harness around Claude Code for writing in one person's name: LinkedIn articles and posts, bios, replies and any other text. The agent drafts; the harness decides what it may claim, checks every word it writes, and turns each correction into a rule or a test so the same mistake can't pass twice.

It is the public build of a private repo its author uses every day. The workflows, rules, checks, tests and hooks are the same files; what stays private is listed under [This build](#this-build). A publish tool builds this repo from the private one and refuses to publish while a private name, an email, a path or a secret is in what would ship.

## How it works

### The mental model: the content loop

Every piece, from a short post to a long article, goes through the same six stages. The channel changes the shape and the length; the loop stays the same. Each stage is described in [`docs/mental-model.md`](docs/mental-model.md).

```
  1 GATHER   ->   2 FRAME   ->   3 SHAPE   ->   4 SHOW   ->   5 CHECK   ->   6 SHIP
  evidence        reader,        the arc       visuals and    facts, voice,   package,
  ledger          takeaway,      for the       where each     rules, render   preview,
                  terms table    channel       one goes       and look        log
                                                                   |
                                                                   +--> back to 3 or 4 when a check fails
```

### What wraps the loop

- **Evidence first.** A piece may only state what its evidence ledger traces to a source or to the user's own words. A gap becomes a visible `[CHECK: ...]` or `[YOUR MOMENT: ...]` marker, never a plausible guess.
- **One rule set, in one order.** The user's own rules win, then the hard house rules, then the voice guides, then the defaults ([`system/00-core/house-rules.md`](system/00-core/house-rules.md)). Every hard rule has an `HR-` ID, and any copy of a rule names it.
- **A linter and an LLM-as-a-judge.** [`scripts/test_check_text.py`](scripts/test_check_text.py) is a regex linter for what a pattern can see: dashes, banned phrases, slogans, montage openings, AI-writing patterns with a score. [`scripts/ai_review.py`](scripts/ai_review.py) sends what it can't see (tone, a pitch, an unsupported claim, the voice) to a model with a rubric, and is calibrated on the user's own corrections before its verdict counts.
- **Hooks, not reminders.** Claude Code hooks lint a file after every write, check changed files and quoted chat text before a turn ends, deny a commit with errors, and ask before any rule file changes ([`.claude/settings.json`](.claude/settings.json)).
- **Corrections become tests.** Each correction the user makes becomes a house rule, a case in [`tests/feedback/cases.json`](tests/feedback/cases.json), or both. The cases that ship come from the house rules' own examples and from drafts of one LinkedIn article. A rules lock fails CI when a rule, a banned phrase, an error type or a case disappears without the lock changing in the same commit, so a check can't quietly get weaker.

The full reference (layers, back end, APIs, evals, tests, guardrails, known limits) is [`docs/harness.md`](docs/harness.md); the guardrails in depth are in [`docs/guardrails.md`](docs/guardrails.md).

## Commands

| Command | What it does |
|---|---|
| `/write-linkedin-article` | a long-form LinkedIn article through the full loop |
| `/write-linkedin-post` | a post of 200 words at most, from a post type when one fits |
| `/write-text` | anything else in the user's name: a reply, a bio, a message |
| `/plan-visuals` | which visuals a draft needs and exactly where each one goes |
| `/check-draft` | the linter, the structure check and the AI reviewer on a draft (read-only) |
| `/content-status` | what is in progress and what waits for the user (read-only) |
| `/add-voice-sample` | add a published post to the voice library and rebuild the voice guide |

## Set it up

1. Clone it and open it in Claude Code (`claude` in the folder). The hooks and the rules load on their own.
2. Fill in your facts in `workspace/profile/`: `MY_PROFILE.md`, `MY_RULES.md` (confidentiality comes first), `GOALS.md`, `cv-master.md`. Paths are set in `config.yaml`; point them elsewhere if your facts live in another repo.
3. Add your voice: create `workspace/tone-of-voice/` (its paths are the `voice:` keys in `writing-rules.yaml`), add a few of your own published posts to `social/` there, and `/add-voice-sample` builds your social voice guide from them (template: `system/00-core/templates/social-voice-template.md`). Your own writing rules go in `MY_WRITING_RULES.md` in that folder, and win over every default.
4. Check the setup: `python3 scripts/doctor.py`, then `python3 -m unittest discover -s tests`. Everything is standard-library Python; the AI reviewer also needs the `anthropic` package and an API key, or the Claude CLI.

The sibling repos in `config.yaml` are optional: a design repo that renders images (design-assistant, its git URL in `config.yaml`) and any repo a piece is about.

## This build

The author's own install has more than ships here. Left out of this build: a job applications module (the CV, cover letter and outreach wording rules do ship), modules for portfolio case studies and blog posts, the author's own tooling outside this repo, the author's voice, pieces, profile and reviewer calibration, and a post type written from the author's own career.

A fresh install has no calibration record, so the AI reviewer starts uncalibrated and the test that compares the record with the reviewer is skipped until the first run (`python3 scripts/test_calibrate_reviewer.py`).

## Licence

MIT, see [`LICENSE`](LICENSE).
