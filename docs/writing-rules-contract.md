# The writing rules contract

This repo owns every rule for how the user's text is written, and the user's voice. Other repos read those rules through a small, versioned file, `writing-rules.yaml`, and never through the paths behind it. Set up on 2026-11-24.

## The decision


The design is borrowed from service design. Each concern has one owner. The owner publishes an explicit, versioned contract. A consumer depends on the contract, never on the owner's internals, and each deployment of a consumer chooses its own binding to the owner. A deployment that cannot reach the owner gets a pinned artifact with checksums instead.

Other ways were weighed:

- **Copies in each repo** are simple and work offline, and that is how the rules spread before: the staccato rule ended up in four files, each worded differently, and `doctor.py` had to scan them for drift.
- **A git submodule** pins an exact commit, which is what a published product wants. For the user's own repos it means a second commit for every rule change, and a nested repo inside the profile repo.


## The contract: writing-rules.yaml

The file is at the root of this repo. A provider is any folder with a `writing-rules.yaml` at its root: schema 1, flat keys, each a path relative to that folder. The key names are the ones the workflows here already wrote in braces, so a workflow says `{social_voice}` in every repo.

| Key | Section | Path in this repo | What it is |
|---|---|---|---|
| `house_rules` | rules | `system/00-core/house-rules.md` | the rules for every channel, each with an `HR-` ID |
| `banned_phrases` | rules | `system/00-core/banned-phrases.txt` | the phrases `test_check_text.py` refuses |
| `social_voice_rules` | rules | `system/00-core/social-voice-rules.md` | the rules for social posts |
| `cv_rules` | rules | `system/40-job-applications/cv-rules.md` | how a CV's words read |
| `cover_letter_rules` | rules | `system/40-job-applications/cover-letter-rules.md` | how a cover letter reads |
| `outreach_rules` | rules | `system/40-job-applications/outreach-rules.md` | how a networking message reads |
| `voice_library` | rules | `system/00-core/voice-library.md` | the workflow that keeps the samples and builds the guide |
| `social_voice_template` | rules | `system/00-core/templates/social-voice-template.md` | the template of the guide |
| `tone_of_voice` | voice | `workspace/tone-of-voice/TONE_OF_VOICE.md` | the user's general tone of voice guide |
| `voice_samples` | voice | `workspace/tone-of-voice` | the user's writing samples |
| `social_voice` | voice | `workspace/tone-of-voice/social/SOCIAL_VOICE.md` | the user's social voice guide |
| `social_samples` | voice | `workspace/tone-of-voice/social` | the user's published posts |
| `social_inspiration` | voice | `workspace/tone-of-voice/social-inspiration` | others' posts, anonymized |
| `writing_overrides` | voice | `workspace/tone-of-voice/MY_WRITING_RULES.md` | the user's own writing rules, which win over every other one |

Its rules:

- **`rules:` files are generic.** They name no person, employer or customer, and no path outside the contract. A pointer to another contract file or to a voice file is the key in braces (`{social_voice}`, `{writing_overrides}`). `{profile}` and `{rules}`, the user's profile and own rules, are the two keys outside the contract a rules file may use, since every consumer has them.
- **`voice:` files are the user's own** and never leave this repo.
- **Schema 1 grows by adding a key.** Renaming or removing one is schema 2, and both sides change together.
- **Each path is written once.** `config.yaml` keeps the sibling repos and the user's facts (`profile`, `goals`, `rules`, `cv_master`, `portfolio_stories`); `scripts/doctor.py` reads both files, so every `{key}` in a workflow resolves.

`tests/test_writing_rules_contract.py` checks all of it in CI: schema 1, every rules file present, no key in both files, the rules files generic, every `{key}` they use known, the house rule IDs unique. `python3 scripts/doctor.py` reports a missing rules file, a schema other than 1 and a key written twice, and exits 1 for any of them; a missing voice file is a warning.


## How a rule changes and reaches each consumer

1. **Here.** A rule changes in a pull request, house rules first: the project hook asks before a rule file changes, `tests/rules.lock` changes in the same commit, and CI must pass before the merge.
2. **The user's own sessions.** They read the files on disk: this repo's hooks and imports and the `writing-rules` skill in the user's personal skills. Pulling this repo's `main` after the merge is what makes the change live there.

## What a new consumer has to do

- Choose a binding per deployment: a path to a clone of this repo where it can be reached, and a pinned pack where it cannot.
- Keep restated rules out. Where a hard stop has to be at the top of a workflow, one line that cites the rule's ID (`HR-no-dashes`) is enough, and `scripts/test_rule_sync.py` can scan that file.
- Never copy a voice file out of this repo.

## Limits

- **Files on disk, not a service.** A clone behind its remote gives the older rules until it is pulled, the same as before.
- **The YAML is a two-level subset,** read by hand in standard-library Python: no lists, no anchors, no nesting below a section.
- **Precedence is stated once,** in the house rules' opening paragraph, and every consumer has to point to it rather than restate it; `doctor.py` cannot see a consumer that does otherwise.
- **Schema 2 is not defined yet.** The first rename of a key will need it, and a migration in each consumer.
