# Workflow: LinkedIn post

**Trigger:** "Draft a LinkedIn post about [X]" / "Turn this idea into a post" (`/write-linkedin-post`)

A short post (200 words at most) with one point and one image. Run the content loop (`system/00-core/content-loop.md`). The post rules are `{social_voice_rules}`: read them in full before drafting. They win over this file wherever the two differ, and the user's own writing rules (`{writing_overrides}`) win over both. A post type (Step 0) sits between the post rules and this file: it wins over this file and gives way to the post rules, with the two exceptions in `post-types/README.md`: a lower word cap with no minimum length, and a rule the user set for that type, which the type lists.

## Step 0: Folder and post type

1. **Post type.** List the files in `system/20-linkedin-posts/post-types/` at run time (every `.md` file but `README.md`) and read the "Use it when" line of each. When one matches the idea, or the user names one, follow that file from here on: it says what it changes in Steps 1 to 6. When none matches, use the standard arc in Step 3. When the draft is shown, say which type was used, or that none was.
2. Draft template: the one the type names, otherwise `system/20-linkedin-posts/templates/post.md`, copied as `draft.md`. Final copy: `post.md`.

## Step 1: Gather

1. The idea: what the user named, a file in `workspace/ideas/`, or the ideas location named in the user's own writing rules, `{writing_overrides}` (a Drive folder: read it, never edit, move or delete it).
2. The voice, in this order: `{social_voice_rules}`, `{social_voice}` in full (the session start loads it without its Images and Techniques sections, so read those from the file), `{tone_of_voice}`. The guide is built from the user's posts in `{social_samples}` and the inspiration posts in `{social_inspiration}`; read those only to refresh it, not for each post (`HR-voice-guide-first`).
3. `{profile}` and `{rules}` for facts and confidentiality.
4. **The real detail:** every post includes one real detail from the user's own work (`{writing_overrides}`). Find it in the idea. If the idea has none, ask the user for one before drafting, or leave `[CHECK: real detail]` where it goes. A feature description from a product page is never the detail.

## Step 2: Frame

The brief is short for a post: reader, the one point, the takeaway, the real detail, the terms table if the post uses a niche term.

## Step 3: Shape: the post arc

The standard arc, for a post with no type; a post type replaces it with its own lines.

| Beat | What it does |
|---|---|
| Hook | the first two lines, about 200 characters: the point, a stance or a concrete situation, in full sentences (one short fragment as a second beat is fine; a montage or a staccato run is not) |
| The detail | the real moment from the user's work that proves the point |
| What it means | one or two short paragraphs: what it changes for the reader's own work, in the field's terms |
| Close | one: a real question, an offer to talk, or one practical warning |

Plus two other hooks the user can swap in.

The register is `system/00-core/house-rules.md`, section 3: AI and tech terms without definitions, nothing explained down, and a practitioner sharing what they saw, never a pitch for the tool.

## Step 4: Show

One image, `v1`, position "post image".
1. **The user's own image first:** a screenshot or photo that came with the idea. Suggest a crop or annotation if it helps.
2. **Otherwise design-assistant:** `/explainer --format=poster` at 1080x1350 for an idea, `/architecture-diagram` for a system, or a 1200x627 side-by-side for a comparison. At most 8 words on the image.
3. Alt text, always.

## Step 5: Check

`python3 scripts/test_check_text.py <draft.md> --max-words 200 --visuals <visuals.md>`, with the post type's cap in place of 200 when it sets one. The count covers hook to close; the hooks list, image brief and alt text sit outside the `## Post` section and are not counted (the script counts only that section when it exists). Over 200: merge or drop the paragraph that repeats the hook, then the weakest example. Never cut the close.

Then the self-check in `{social_voice_rules}`, section 6.

## Step 6: Ship

`post.md` as the user will paste it. When `{writing_overrides}` names a Drive folder for final posts, also export the post there as a Google Doc: the Drive connector's `create_file` with `parentId` set to that folder's id, `contentMimeType` `text/html` and the post as simple HTML in `textContent` (an `<h1>` title, a `<p>` per paragraph, `<br>` for a line break inside one), which Drive converts into a Google Doc. Title it `LinkedIn post - YYYY-MM-DD - [Topic]`. Before creating it, `search_files` that folder for the same title; if it exists, say so and update that doc rather than adding a duplicate. With no folder named or no connector, keep `post.md`, say where it is, and offer to record a Drive folder in `{writing_overrides}`. Give the user the link to every Google Doc created, and never say a post reached Drive when it did not. Log the post in `workspace/content-log.md`. After it is live, offer `/add-voice-sample mine`.
