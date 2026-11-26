# Sibling repos: who does what

This repo decides what to say and what to show. The sibling repos do the specialist work. Their paths and git URLs come from `config.yaml`; `scripts/repos.py` clones a missing one and fast-forwards the rest, so the link works on a laptop and in a cloud session alike.

**Why not git submodules:** a submodule pins each sibling to one old commit, needs a second commit here every time a sibling changes, and turns a write in the profile repo (a CV, an application) into a commit inside a nested repo. The siblings change daily and are worked on directly, so they are linked by URL and always used at their latest `main`.

| Repo | What this repo takes from it | What this repo asks it to do | What this repo never does there |
|---|---|---|---|
| **design-assistant** | brand rules (`docs/brand.md`), the command catalogue (`.claude/commands/`), generators | make every visual outside the portfolio site: `/visual-brief` to choose, then `/explainer`, `/card-illustration`, `/architecture-diagram`, `/one-pager` or `/placeholder` | change its brand rules or generators to suit one piece; suggest that as a separate change instead |
| **Portfolio** | the page structure and CMS fields (`src/integrations/supabase/types.ts`, `AGENTS.md`, `supabase/content/`) | take finished case-study copy and apply it the way its `AGENTS.md` says (fresh export first, a content script in `supabase/content/`); make the site's images with its design-assets tools and templates | write to the database; push to `main`, which deploys through Lovable |
| **company-brain** (optional) | facts for pieces about Company Brain | nothing | write notes in it |


