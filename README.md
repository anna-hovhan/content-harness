# Content harness

A harness around Claude Code for writing in one person's name: LinkedIn articles and posts, portfolio case studies, blog posts, bios and replies. The agent drafts; the harness decides what it may claim, checks every word it writes, and turns each correction into a rule or a test so the same mistake can't pass twice.

It is the public build of a private repo its author uses every day. The workflows, rules, checks, tests and hooks are the same files; the author's voice, pieces, profile and the job application module stay private. A publish tool builds this repo from the private one and refuses to publish while a private name, an email, a path or a secret is in what would ship.

## How it works

Every piece runs the same six-stage loop, whatever the channel ([`docs/mental-model.md`](docs/mental-model.md)):

```
  1 GATHER   ->   2 FRAME   ->   3 SHAPE   ->   4 SHOW   ->   5 CHECK   ->   6 SHIP
  evidence        reader,        the arc       visuals and    facts, voice,   package,
  ledger          takeaway,      for the       where each     rules, render   preview,
                  terms table    channel       one goes       and look        log
```

- **Evidence first.** A piece may only state what its evidence ledger traces to a source or to the user's own words. A gap becomes a visible `[CHECK: ...]` or `[YOUR MOMENT: ...]` marker, never a plausible guess.
- **One rule set, in one order.** The user's own rules win, then the hard house rules, then the voice guides, then the defaults ([`system/00-core/house-rules.md`](system/00-core/house-rules.md)). Every hard rule has an `HR-` ID, and any copy of a rule names it.
- **A linter and an LLM-as-a-judge.** [`scripts/test_check_text.py`](scripts/test_check_text.py) is a regex linter for what a pattern can see: dashes, banned phrases, slogans, montage openings, AI-writing patterns with a score. [`scripts/ai_review.py`](scripts/ai_review.py) sends what it can't see (tone, a pitch, an unsupported claim, the voice) to a model with a rubric, and is calibrated on the user's own corrections before its verdict counts.
- **Hooks, not reminders.** Claude Code hooks lint a file after every write, check changed files and quoted chat text before a turn ends, deny a commit with errors, and ask before any rule file changes ([`.claude/settings.json`](.claude/settings.json)).
- **Corrections become tests.** Each correction the user makes becomes a house rule, a case in [`tests/feedback/cases.json`](tests/feedback/cases.json), or both. A rules lock fails CI when a rule, a banned phrase, an error type or a case disappears without the lock changing in the same commit, so a check can't quietly get weaker.

The full reference (layers, back end, APIs, evals, tests, guardrails, known limits) is [`docs/harness.md`](docs/harness.md); the guardrails in depth are in [`docs/guardrails.md`](docs/guardrails.md).

## Commands

| Command | What it does |
|---|---|
| `/write-linkedin-article` | a long-form LinkedIn article through the full loop |
| `/write-linkedin-post` | a post of 200 words at most, from a post type when one fits |
| `/write-portfolio-page` | case study copy keyed to a portfolio site's CMS fields |
| `/write-blog-post` | a post for the site's blog, at most a 4-minute read |
| `/write-text` | anything else in the user's name: a reply, a bio, a message |
| `/plan-visuals` | which visuals a draft needs and exactly where each one goes |
| `/check-draft` | the linter, the structure check and the AI reviewer on a draft (read-only) |
| `/content-status` | what is in progress and what waits for the user (read-only) |
| `/add-voice-sample` | add a published post to the voice library and rebuild the voice guide |

## Set it up

1. Clone it and open it in Claude Code (`claude` in the folder). The hooks and the rules load on their own.
2. Fill in your facts in `workspace/profile/`: `MY_PROFILE.md`, `MY_RULES.md` (confidentiality comes first), `GOALS.md`, `cv-master.md`. Paths are set in `config.yaml`; point them elsewhere if your facts live in another repo.
3. Add your voice: a few of your own published posts in `workspace/tone-of-voice/social/`, then `/add-voice-sample` builds `SOCIAL_VOICE.md` from them. Your own writing rules go in `workspace/tone-of-voice/MY_WRITING_RULES.md`, and win over every default.
4. Check the setup: `python3 scripts/doctor.py`, then `python3 -m unittest discover -s tests`. Everything is standard-library Python; the AI reviewer also needs the `anthropic` package and an API key, or the Claude CLI.

The sibling repos in `config.yaml` are optional: a design repo that renders images ([design-assistant](https://github.com/anna-hovhan/design-assistant)), your site's repo for portfolio pages, and any repo a piece is about.

## The worked example

[`workspace/pieces/2026-11-12-company-brain-article-refined/`](workspace/pieces/2026-11-12-company-brain-article-refined/) is a published article with its brief, evidence ledger, draft, placement map and cover, the piece the mental model was taken from. Most of the feedback cases come from its earlier drafts.

## Licence

MIT, see [`LICENSE`](LICENSE).
