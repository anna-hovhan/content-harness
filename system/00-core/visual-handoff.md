# Workflow: visual handoff

**Trigger:** step 4 of the content loop, or "Which visuals does this need?" / "Where do the images go?" (`/plan-visuals`).

This repo plans every visual and says exactly where it goes. design-assistant makes it (Step 2). Never draw a visual in this repo, and never change its design rules to fit one piece.

## Step 1: Find the beats that need a picture

Read the draft and the brief. A beat gets a visual when:
- it is **the thesis** (the cover of an article, the image of a post), or
- it is **a hard idea** words explain badly: a structure (layers, a system), a sequence (a weekly rhythm, a pipeline), a comparison.

A beat that is easy in words gets no picture. Typical counts: a post 1, an article 1 cover plus 1 to 3.

## Step 2: Choose the design system, then the command

| Shown on | Design system | Made in |
|---|---|---|
| posts, articles, one-pagers, slides, heroes, covers, decks | AH Visuals (light glass or deep blue gradients, Syne) | design-assistant, with the commands below |

Use design-assistant's own decision rule (`{design_commands}/visual-brief.md`):

| The point of the visual | Command |
|---|---|
| how parts of a system relate | `/architecture-diagram` |
| an idea the reader does not know yet | `/explainer` (`--format=poster` for one image, `scroll` or `slides` for a page) |
| a printable summary to keep | `/one-pager` |
| a cover that shows what a project does | `/card-illustration` |
| only a named cover image is missing | `/placeholder` |

For an article cover, use `/card-illustration` line style at the channel's cover size, with the title set as text (it is rendered to PNG, so web fonts work). Sizes come from `docs/channels.md`.

## Step 3: Write the placement map

Fill `visuals.md` in the piece folder, one row per visual:

| Field | What goes in it |
|---|---|
| id | `v1`, `v2`, ... in reading order; `v1` is the cover or the post image |
| slug | short name, the same as in the draft marker |
| beat | the idea it carries, in one line |
| command | the command and its arguments, exactly as it will be run, and the repo it runs in |
| size | width x height and scale, from `docs/channels.md` |
| file | where the output is saved (the piece's `visuals/` folder, design-assistant `out/`) |
| position | where it goes: "article cover", "post image", or "after the sentence: '<exact sentence>'" |
| copy | the headline and any text on the image, using the terms table |
| alt text | one or two plain sentences describing what is in the image |
| caption | optional, one short line |

Then put each marker in the draft on its own line, directly after the sentence named in **position**: `[IMAGE v2: three-floors]`. `scripts/test_check_text.py --visuals` fails when a marker has no row or a row has no marker.

## Step 4: Make each visual

1. Open design-assistant (`{design_assistant}`) and follow the chosen command's file in `.claude/commands/` and its brand rules (`{brand}`).
2. Pass the brief: the beat, the copy, the size, and the facts from the evidence ledger the visual shows.
3. Save the source (HTML or SVG) next to the exported image so it can be edited and re-exported later.

## Step 5: Render and look

Render at the final size (2x for in-article images, 1x for covers whose pixel size is set by the channel) after the fonts have loaded, and look at the image. Check:
- no text overflows its column or runs into the art
- no single word stranded on a line of a heading
- gradients and accents cover what they should
- connectors start and end on their shapes
- no large empty band left at an edge
- every word on the image matches the text and the terms table, and follows the house rules

Fix, render again, then show the user.
