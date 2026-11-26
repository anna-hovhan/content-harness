# Workflow: portfolio page

**Trigger:** "Write the portfolio page for [project]" / "Update the [project] case study" / "Write the card for [project]" (`/write-portfolio-page`)

Copy for a case study on the portfolio site, and the card that leads to it, written to the site's own structure. Run the content loop (`system/00-core/content-loop.md`); this file adds what the site needs.

The site's content lives in its CMS (Supabase), not in files. This workflow writes `page.md`, copy keyed to the CMS fields, and stops there. The Portfolio repo applies it the way its `AGENTS.md` says: a fresh export of the affected tables first, then a content script in `{portfolio_content_scripts}`. Never write to the database from here.

**Worked example of a finished page:** `{portfolio_content_scripts}/20261026_company_brain_copy.sql` (the Company Brain case study: hero, stat cards, section titles, challenge and solution bullets, custom sections, image captions).

## Step 0: Folder

Draft template: `system/30-portfolio-pages/templates/case-study.md`, copied as `draft.md`. Final copy: `page.md`.

## Step 1: Gather

1. The project's own sources: its repo, docs, the user's notes.
2. The user's story for it in `{portfolio_stories}` and the matching bullets in `{cv_master}`, so the page, the CV and any post tell the same facts.
3. The site's structure: `{portfolio_schema}` for the field names, `{portfolio_agents}` for the rules (project types, home sections, how sections are ordered). If the project already has a page, ask the user for the current copy or a fresh export; never guess what is live.
4. Confidentiality: the site removed client and employer detail and internal metrics on 4 Nov 2026 (`{portfolio_content_scripts}/README.md`). Follow `MY_PROFILE.md`, `MY_RULES.md` and that precedent: no customer names, no internal figures the user has not cleared.

## Step 2: Frame

The reader is a hiring manager or a potential client who has 60 seconds. The brief names the role family the page supports (from `{goals}`) and the strength it proves.

## Step 3: Shape: the case-study arc

The page's sections, in the site's order. The field each one fills is in brackets.

| Beat | Field | What it does |
|---|---|---|
| Card | `projects.card_title`, `projects.card_summary` | the project and its point, for the Selected work grid |
| Hero | `projects.title`, `projects.description`, `projects.role`, `projects.tags` | what it is and the user's role, in two sentences |
| At a glance | `project_details.tldr_problem`, `tldr_role`, `tldr_result` | problem, role, result, one line each |
| Stat cards | `project_metrics` (value, label) | up to 4 numbers that are true and cleared |
| The problem | `project_details.context` (title in `section_titles.context`) | a concrete situation, then why it is common |
| Why it's hard | `project_section_items`, section `challenge` | 2 to 4 bullets |
| Custom sections | `project_custom_sections` (title, subtitle, body, placement `top`, `after_challenge` or `bottom`) | "Who it's for", "Where I started", "Key decisions", "Honest limits", where to see the work or get in touch |
| How it works | `project_section_items`, section `what_i_did` | 3 to 6 bullets, each starting with a short bold-able phrase |
| Proof | `project_details.results` | what was shown, how, and what it proves |

Also set: `projects.type` (one or two of: AI strategy, AI systems, Delivery and immersive; the database enforces this list) and `projects.work_collection` (`selected_work` or `earlier_work`).

Voice: first person, direct, specific, in the field's terms (`system/00-core/house-rules.md`, section 3). A case study shares how the work was done: show decisions and trade-offs, and include honest limits. The lessons a reader can use beat a list of features.

## Step 4: Show

Images for the site use its own design system and the Portfolio repo's tools, never design-assistant (`system/00-core/visual-handoff.md`, Step 2).

| Visual | Made with (Portfolio repo) | Position |
|---|---|---|
| Selected work thumbnail | the `case-study-thumbnail` skill, from `design-assets/templates/case-study-thumbnail.svg` | `projects.card_image_url` |
| Link preview image | the `og-image` skill, from `design-assets/templates/og-image.html` | `projects.share_image_url` |
| Architecture, system or concept diagram | `node scripts/design-assets.mjs diagram`, in the design system's diagram grammar | a solution image (`project_solution_images`), with its order and caption |

Each row in `visuals.md` names the CMS section and the order inside it, and a caption (`project_solution_images.caption`). Storage upload and `image_url` changes are the user's: a new file gets a new name, never the name of a file already in Storage (Portfolio `docs/design-assets.md`).

## Step 5: Check

The page goes on the portfolio site: no private repo is named or described, and no repo-internal specifics appear (the dates of internal events, rule IDs, file and script names, counts, quotes from the repo). (`HR-site-private-repos`)

`python3 scripts/test_check_text.py <draft.md> --visuals <visuals.md>`. Then check every stat card against the evidence ledger and the confidentiality rules, and that `projects.type` uses only the allowed values.

## Step 6: Ship

`page.md` with one heading per field, ready for the Portfolio repo to turn into a content script. Tell the user the next steps there: take a fresh export of the affected tables, write the script in `supabase/content/`, review, run it in the Supabase SQL editor. Offer to do the script in the Portfolio repo as a separate task.
