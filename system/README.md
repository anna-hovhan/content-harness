# System: stage map

Generic workflows, the same for anyone. Nothing personal belongs here.

| Folder | What | Entry point |
|---|---|---|
| `00-core/` | the content loop every module runs, house rules, banned phrases, the social voice rules, the voice library workflow (`/add-voice-sample`) and its guide template, visual handoff (design-assistant, or the Portfolio repo for site images), shared templates (brief, evidence ledger, placement map) | `content-loop.md` |
| `10-linkedin-articles/` | long-form articles: the article arc, cover and explainers | `linkedin-article.md` |
| `20-linkedin-posts/` | posts of 200 words at most, one image; `post-types/` holds one blueprint per kind of post (leaving a job, for example), which the workflow finds by listing the folder | `linkedin-post.md` |
| `30-portfolio-pages/` | case-study copy keyed to the site's CMS fields | `portfolio-page.md` |
| `35-blog-posts/` | posts for the site's blog: the article arc, the blog's CMS fields, cover and diagrams in the site's design system | `blog-post.md` |
| `40-job-applications/` | the wording rules for a CV, a cover letter and an outreach message (`cv-rules.md`, `cover-letter-rules.md`, `outreach-rules.md`) | `cv-rules.md` |
| `50-other-text/` | any text the other modules do not cover: a comment, a reply, a message, a bio, an about page, alt text (`/write-text`) | `other-text.md` |

Every rules file and voice file is a key of the writing rules contract, `writing-rules.yaml` at the repo root (`docs/writing-rules-contract.md`).

The reasoning behind the loop is `docs/mental-model.md`; channel sizes and limits are `docs/channels.md`.
