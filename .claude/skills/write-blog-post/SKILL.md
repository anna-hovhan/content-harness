---
description: Write a post for my portfolio site's blog that shares one thing I built, tried or think, with a cover and diagrams in the site's design system placed in the text
argument-hint: '"<topic, repo or idea>" [--reader=...]'
disable-model-invocation: true
---

Write a blog post for my site about: $ARGUMENTS

1. Read `AGENTS.md` (session start) and `docs/mental-model.md` if they are not loaded yet.
2. Run `system/35-blog-posts/blog-post.md`, which runs the content loop in `system/00-core/content-loop.md` with the article arc.
3. A case study is another piece: `/write-portfolio-page`. When I want both, make two piece folders and link them once both are live.
4. Never write to the site's database. The output is `article.md`; applying it is a separate task in the Portfolio repo, following its `AGENTS.md`.
5. End with the takeaway sentence, the open `[YOUR MOMENT]` and `[CHECK]` markers, and where each image goes.
