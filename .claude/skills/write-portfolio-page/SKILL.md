---
description: Write portfolio case-study copy and its card, keyed to the site's CMS fields, with the visuals each section needs
argument-hint: '"<project name>" [--update]'
disable-model-invocation: true
---

Write the portfolio page for: $ARGUMENTS

1. Read `AGENTS.md` (session start) if it is not loaded yet.
2. Run `system/30-portfolio-pages/portfolio-page.md`. Field names come from the Portfolio repo (`portfolio_schema` in `config.yaml`).
3. A blog post on the same subject is another piece: `/write-blog-post`. When I want both, make two piece folders and link them once both are live.
4. Never write to the site's database. The output is `page.md`; applying it is a separate task in the Portfolio repo, following its `AGENTS.md`.
