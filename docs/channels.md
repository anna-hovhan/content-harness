# Channels: sizes, limits and image positions

What each channel allows, and where images can go in it. Workflows read this when they write the placement map. When one of the user's own writing rules (`{writing_overrides}`, `workspace/tone-of-voice/MY_WRITING_RULES.md`) differs, it wins.

## LinkedIn article

| Item | Spec |
|---|---|
| Cover image | 1920x1080 PNG at 1x (16:9). Keep the title and key art clear of the outer 40px top and bottom: link previews crop the cover to about 1.91:1 |
| In-article images | landscape, 1600px wide designs exported at 2x (3200px), PNG. Each sits on its own line between paragraphs |
| Image positions | the cover is uploaded separately as the article cover; in-article images go at their `[IMAGE vN: slug]` markers, each directly after the sentence named in `visuals.md` |
| Captions | optional, one short line under each in-article image |
| Length | no hard cap; aim for 1,000 to 1,600 words so it reads in about 6 minutes |
| Hashtags | up to about 7 at the end, only if the user's samples use them |

## LinkedIn post

| Item | Spec |
|---|---|
| Text | at most 200 words, hook to close (`{writing_overrides}`), counted with `scripts/test_check_text.py --max-words 200` |
| Hook | the first two lines, about 200 characters: what shows before "...see more" |
| Image | exactly one, attached to the post (position: the post image). Portrait 1080x1350 takes the most feed space; square 1200x1200; a side-by-side comparison suits 1200x627 |
| Image text | at most 8 words, same house rules as the post |
| Alt text | always, one or two plain sentences |
| Real detail | every post includes one real detail from the user's own work (`{writing_overrides}`) |
| Post types | a post type can set a lower word cap and no minimum length, and it lists any rule you set for it that differs from the post rules; each type's file in `system/20-linkedin-posts/post-types/` gives its goal, its cap and its check command |

## Portfolio site

Content lives in the site's CMS (Supabase), not in files. The field names below are the CMS columns; the Portfolio repo's `AGENTS.md` and `src/integrations/supabase/types.ts` are the authority if they change.

| Item | Spec |
|---|---|
| Selected work thumbnail | 320 x 200 SVG from the Portfolio repo's `case-study-thumbnail` template, in the site's design system (`projects.card_image_url`) |
| Card without an image | no image: the card shows text only; the site has no placeholder images |
| Link preview image | 1200 x 630 PNG from the Portfolio repo's `og-image` template (`share_image_url`); never shown on a page |
| Case-study hero | `projects.image_url` (and `hero_aspect_ratio`) |
| Solution images | rows in `project_solution_images`, each with a caption; their position comes from `project_details.layout_blocks` |
| Architecture diagrams | the Portfolio repo's `scripts/design-assets.mjs diagram`, in the design system's diagram grammar (dark) |
| Image positions | name the CMS section each image belongs to (`what_i_did` / "How it works", a custom section by title) and its order inside it |

## Portfolio blog article

A post on the site's blog (`/write-blog-post`). Its content is in the CMS table `blog_posts`.

| Item | Spec |
|---|---|
| Title | `title`, with an optional `title_accent` for the second half of a two-part title |
| Summary | `summary`: one or two sentences, shown on the blog index and in link previews |
| Tags | `tags`: up to four |
| Cover | `cover_image`: a PNG 1920 wide, exported from a 960 x 540 diagram in the site's design system, with alt text |
| In-text images | SVG diagrams from the Portfolio repo's `scripts/design-assets.mjs diagram`, each in an images block with alt text and a caption, at its `[IMAGE vN: slug]` marker |
| Text | paragraphs, `##` headings, lists and one callout; markdown links render |
| Length | at most 880 words, a 4-minute read at the site's 220 words a minute, for posts from 2026-11-25 (`{writing_overrides}`); `test_check_pieces.py` enforces it in CI |
| Visibility | a new post is hidden until it is set to Show in the admin |

## Other text (`/write-text`)

A comment, a reply, a message, a bio, an about page, alt text on its own: no fixed size. Use the platform's own limit and any limit in `{writing_overrides}`, count words with `scripts/test_check_text.py --max-words N`, and pass `--channel` when the text is a LinkedIn post, which renders no markdown. Plain text unless the platform renders more.

## CV and cover letter

No images. Format, length (2 pages at most), ATS rules and export are owned by the profile repo (`AGENTS.md` and `system/50-applications/` there). The wording rules are in this repo: `{cv_rules}` and `{cover_letter_rules}`. A cover letter may link one portfolio case study; check the link is public first.
