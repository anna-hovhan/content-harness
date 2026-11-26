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

## Other text (`/write-text`)

A comment, a reply, a message, a bio, an about page, alt text on its own: no fixed size. Use the platform's own limit and any limit in `{writing_overrides}`, count words with `scripts/test_check_text.py --max-words N`, and pass `--channel` when the text is a LinkedIn post, which renders no markdown. Plain text unless the platform renders more.

## CV and cover letter

No images. Format, length (2 pages at most), ATS rules and export are owned by the tool that makes them. The wording rules are in this repo: `{cv_rules}` and `{cover_letter_rules}`. A cover letter may link one portfolio case study; check the link is public first.
