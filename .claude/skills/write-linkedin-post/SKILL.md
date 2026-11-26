---
description: Turn an idea into a LinkedIn post of 200 words at most, in my social voice, with one image and its alt text. A post type in system/20-linkedin-posts/post-types/ shapes the post when one fits the idea.
argument-hint: "<idea, idea file or Google Doc URL; a post type to use, if any>"
disable-model-invocation: true
---

Write a LinkedIn post for: $ARGUMENTS

1. Read `AGENTS.md` (session start) if it is not loaded yet.
2. Run `system/20-linkedin-posts/linkedin-post.md`. Its rules are `social_voice_rules` in `writing-rules.yaml`; read them in full first. Its Step 0 lists the post types and picks the one that fits the idea, or the one named here.
3. Count words with `python3 scripts/test_check_text.py <draft> --max-words 200`, or with the post type's cap when it sets one, never by eye.
4. Show the post as it will look on LinkedIn, which post type it used (or the standard arc), the image (or its design-assistant command), the alt text, two other hooks and any open `[CHECK]`.
