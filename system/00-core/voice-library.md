# Workflow: the voice library

**Trigger:** "Add this post as a voice sample" / "Save this post as inspiration" (the samples command: `/add-voice-sample`, or `/add-social-sample` where that is its name), and "Refresh my social voice"

Keeps the two libraries the user's social writing learns from, the user's own published posts and anonymized posts by others they like, and builds the social voice guide from them. Drafting a post is not part of this workflow.

> **The rules for a post are `{social_voice_rules}`.** Whatever drafts a post reads them first: the hard rules (no em dashes, `HR-no-dashes`; no negative parallelism, `HR-no-negative-parallelism`; no stock AI phrasing, `HR-no-stock-phrasing`; never invent facts, `HR-never-invent`) and how a post stays different from a CV.

---

## Where everything is

Every location is local, and each one is a key of the writing rules contract.

| What | Where |
|---|---|
| **My posts:** the user's own published posts, the voice to match | `{social_samples}` (add Drive or web copies with the samples command, `mine`) |
| **My social voice guide** | `{social_voice}` |
| **Inspiration:** others' posts, anonymized | `{social_inspiration}` (add them with the samples command, `inspiration`) |

**Reading Drive:** take the id from the URL (`/folders/<id>` for a folder, `/d/<id>` for a doc). List a folder with the Drive connector's `search_files` (`parentId = '<id>'`) and read each file with `read_file_content`, which returns the text of Google Docs, PDFs and Word files and can read PNG and JPEG images. Images embedded inside a Google Doc do not come through as text: when an idea doc holds images, its final post says to use them. Without a Drive connector, say so plainly and work from local files or pasted text.

**Ignore in every folder:** `README.md`, the guide itself (`{social_voice}`), dotfiles and subfolders whose name starts with `_`.

---

## Add samples

The user names the kind and gives one or more sources: a Google Doc or Drive file URL, a public post URL, a local file, or pasted text.

### The user's own posts (`mine`)

1. Read each source. For a Drive file, `read_file_content`. For a public post URL, fetch the page and take the post text from it as published (a public LinkedIn post page carries it in its `application/ld+json` block, as `articleBody`); a summary is not a sample, so if only a summary comes back, ask the user to paste the text.
2. Keep the post **exactly as written**: no edits, no typo fixes. Drop only what is not part of the post: notes to self, chat or tool links, tracking parameters.
3. Save it in `{social_samples}` as `YYYY-MM-DD-[topic-slug].md` with this header, the date being when it was posted:

```
# Sample: [one line on what the post is]
# Posted: YYYY-MM-DD
# Image: [what the image showed, or "not captured"]

[the post, exactly as written]
```

4. Then refresh the social voice guide (the next section).

### Others' posts (`inspiration`)

1. Read each source the same way.
2. **Anonymize it:** remove the author's name and headline, every person named or tagged, and anything that identifies the author: their employer, its products and internal project names, their own side projects, their newsletter or podcast name. Replace each with a bracketed role, such as `[Company]`, `[Product]`, `[colleagues, tagged]`, `[side project]`. Keep generic tools and public technologies (Slack, Salesforce, Claude Code), since the post's technique often depends on them.
3. **Never save the link**, the post id or anything that leads back to the author.
4. Save it in `{social_inspiration}` as `[NN]-[what-it-does-slug].md`, numbered in order, with this header:

```
# Inspiration: [one line on the technique, not the topic]
# Format: [text only / text + photo / text + screenshot / ...]
# Image: [what the image showed]
# Why it works: [two or three short lines]
# Borrow: [the technique, in one line]
# Don't borrow: [what would be copying]

[the post, anonymized, otherwise exactly as written]
```

5. Inspiration posts never change how the guide describes the user's own voice. They feed one section of it, "Techniques I borrow": add the new post's Borrow and Don't borrow lines there under the kind of post it shows, and tell the user in one line.

---

## Build or refresh the social voice guide

Run it when the guide (`{social_voice}`) is missing, after new samples of the user's own posts, or when the user asks ("Refresh my social voice").

1. Read every sample in `{social_samples}`. Only the user's own posts count; never inspiration posts.
2. Fill the template, `{social_voice_template}`, from what the samples actually do, quoting short phrases from them as evidence. Describe, don't prescribe: this is how the user writes, not how they should.
3. Rebuild "Techniques I borrow" from the Borrow and Don't borrow lines of every post in `{social_inspiration}`, grouped by the kind of post each shows. It is the only section inspiration posts feed.
4. Keep anything the user wrote into the guide by hand, especially under "Never in my posts". The section "Lines I picked and lines I turned down" is kept by hand as a whole: copy it into the refreshed guide exactly as it is, every entry and its date, and never rewrite, merge or drop an entry from the samples.
5. Save it as `{social_voice}`, show the user the main points in a few lines, and ask if anything is off.
