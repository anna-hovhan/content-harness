# Social Voice Rules

The key rules for anything posted on social media: LinkedIn posts, comments, short updates. They add to the house rules for all writing (`{house_rules}`: no em dashes, `HR-no-dashes`; no AI-style contrast phrases, `HR-no-negative-parallelism`; never invent experience, `HR-never-invent`) and make them concrete for posts.

**Which rule wins:** the order the house rules' opening paragraph sets (`{house_rules}`): the user's own rules first, then the hard rules, then the voice guides, then the defaults. For posts that means: the user's own writing rules (`{writing_overrides}`) override anything here. The user's own social voice guide (`{social_voice}`) overrides the defaults in sections 3 and 4 (length, hashtags, emoji, image style), since it describes how *they* write. The user's general guide, `{tone_of_voice}`, if there is one, applies to posts as well, below `{social_voice}`. The hard rules in sections 1 and 2 apply whatever the guide says: only the user's own writing rules can change them.

---

## 1. A post is not a CV

The most common failure. A post reads like a CV when it lists achievements to an imagined recruiter. It should read like one practitioner telling peers about something they did, saw or think.

- **One point per post.** One experiment, one opinion, one lesson, one thing that happened. If the idea holds two, it is two posts.
- **Show the work, not the title.** "I built the same app twice" beats "As an AI architect with 10 years of experience". Never open with a job title or years of experience.
- **No CV verbs:** spearheaded, drove, leveraged, orchestrated, championed, delivered, owned, enabled, empowered. `HR-voice-posts`
- **At most one number**, and only when it carries the point. A post with three metrics is a CV bullet with line breaks. `HR-voice-posts`
- **No credentials in passing:** certifications, team sizes, budgets and client lists stay out unless the post is about them. `HR-voice-posts`
- **The reader is a peer.** Write the way the user would explain it to a smart colleague over coffee: contractions, plain words, an opinion.
- **First person, the user's own experience.** "I tried", "we found", "I'm not convinced". Never "she", never the brand voice of an employer.

## 2. Hard rules (never break these)

- **No em dashes or en dashes**, anywhere: hook, body, image text, alt text. Use a comma, a colon, a full stop, or rewrite. Search the draft before presenting it. `HR-no-dashes`
- **No negative parallelism or AI-style contrast:** "It's not X, it's Y", "X isn't just A, it's B", "Not because X, but because Y", "Less X, more Y", "This isn't about X. It's about Y.", "X, not just Y", and the "From X to Y" transformation headline. Say what the thing *is*, directly. This applies to text on the image too. `HR-no-negative-parallelism`, `HR-ai-no-unasked-contrast`
- **No stock AI phrasing:** "In today's fast-paced world", "In a world where", "Here's the thing", "The reality is", "At the end of the day", "Let's dive in", "game-changer", "unlock", "delve", "elevate", "supercharge", "I'm thrilled to announce", "humbled", "a testament to". The full list is `{banned_phrases}`. `HR-no-stock-phrasing`
- **No lesson-reveal framing:** "Here's what X taught me about Y", "What building it taught me", "What I learnt", "Lessons I learned". It reads as a template and puts the author on a stage. Give the lesson itself, in the reader's terms, or just make the point. This applies to hooks, titles and headings too. `HR-no-lesson-reveal`
- **No sentence starts with "Here is", "Here's" or "Here are"**, in hooks, titles and headings too: "Here's how it changed...", "Here's what I found", "Here are three lessons". Start with the point itself. `HR-no-here-opener`
- **No inflated significance:** don't make things sound important, profound or life-changing: "Building this changed how I think about...", "What I'd pass on to anyone...", "For the first time...", "rules that matter enormously", "Your colleague will thank you". Say what happened; the reader decides whether it matters. `HR-no-inflation`
- **No statements of the obvious:** cut any sentence a tech reader already knows ("every new chat starts from zero", "AI can make mistakes", "tools will keep changing"). Replace it with the specific detail that is new to them, or drop it. `HR-no-obvious`
- **No slogans:** no matched pairs of short fragments that read like a tagline ("Private by default. Shared on purpose.") and no number pairs ("1 folder, 3 commands", "Three floors, one rule"), in the hook, headings and image text too. Write the idea as an ordinary sentence. `HR-no-slogans`
- **No reveal formula:** "The result? ...", "The kicker? ...", "The best part? ..." as a fragment followed by the answer. A genuine question the user would ask out loud is fine; a manufactured cliffhanger is not. `HR-no-reveal-formula`
- **No tricolon on autopilot.** Three adjectives or three parallel clauses in a row, every paragraph, is the clearest sign of generated text. Use the number of items the content actually has. `HR-no-autopilot-tricolon`
- **No invented facts.** Every claim, number, tool name and anecdote comes from the idea, the user's own files, or something the user confirms. If a draft needs a fact the idea does not give, ask, or leave a visible `[CHECK: ...]` marker. `HR-never-invent`, `HR-mark-unknowns`
- **Confidentiality:** follow every confidentiality note in `MY_PROFILE.md` and `MY_RULES.md`. Customers, colleagues and internal project names that must not be named stay out of the post, the image brief and the alt text. `HR-confidentiality`
- **Never copy an inspiration post.** No sentence, no distinctive phrase, no anecdote. Borrow the technique only (see section 5).

## 3. Shape of a LinkedIn post

Defaults. The user's own samples override them: if they write longer, write longer.

- **Hook: the first two lines**, about 200 characters, which is what shows before "...see more". It states the point, a stance or a concrete situation. No throat-clearing ("I've been thinking a lot lately about...").
- **Body: short paragraphs** of one to three sentences, a blank line between them. Mix short sentences with longer ones; a fragment now and then is fine when the user's samples have them.
- **Specifics over abstractions:** the tool, the step that broke, the thing that surprised the user. `HR-concrete`
- **Close with an invitation or a takeaway**, not a sales pitch: a real question, an offer to talk, or one practical warning. One close, not three. `HR-close-reference-question`, `HR-describe-not-sell`
- **Length:** 120 to 250 words unless the user's samples say otherwise.
- **Hashtags:** none, or up to three at the very end, only if the user's samples use them.
- **Emoji:** only if the user's samples use them, and never as bullet points.
- **Lists:** fine for a setup or steps, plain hyphens, at most one list per post.
- **Mentions:** only people or companies the user wants tagged, and never under a confidentiality note.

## 4. The image

Every post has one image. It earns the click on the post, so it does one job: shows the thing the post is about.

- **Real beats polished.** A screenshot of the actual board, terminal, prototype or setup, or a photo of the real thing, beats a stock photo or a generic illustration.
- **Use the user's own image first.** If the idea came with an image, the post uses it. Suggest a crop or an annotation if it would help; never replace it with something generic.
- **Otherwise write an image brief:** what to show, what to capture or screenshot, any text overlay (at most 8 words), and the format: 1080x1350 (portrait, most feed space) or 1200x1200 (square). A side-by-side comparison suits 1200x627.
- **Text on the image follows the hard rules too**, dashes included.
- **Alt text, always:** one or two plain sentences describing what is in the image, for screen readers. No hashtags, no marketing.

## 5. Inspiration posts

Posts by other people that the user likes, kept anonymized in `{social_inspiration}`. They are a toolbox, never a voice.

- **Borrow techniques:** how the hook sets up a question, how an experiment is framed, how a list of setup items makes a post concrete, how a follow-up post reports results.
- **Never borrow** sentences, phrases, jokes, anecdotes, topics presented as the user's own experience, or the author's tone where it differs from the user's samples.
- **The user's own posts win** wherever an inspiration post and the user's samples pull in different directions.
- **Use them when drafting:** pick at most one or two techniques that fit the idea's shape, from the "Techniques I borrow" section of the user's guide or the posts' own Borrow lines. A post with none is fine; a post stitched from five is not the user's.

## 6. Self-check before presenting a draft

- [ ] One point, stated in the first two lines
- [ ] Reads like the user's own posts, not like their CV (no CV verbs, at most one number, no title or credentials) (`HR-voice-posts`)
- [ ] No em dashes or en dashes anywhere, including image text and alt text (`HR-no-dashes`)
- [ ] No negative parallelism, no lesson-reveal framing ("what X taught me"), no sentence starting with "Here is" / "Here's" / "Here are", nothing inflated, nothing obvious, no slogans, no stock AI phrasing, no reveal formula, no autopilot tricolon (`HR-no-negative-parallelism`, `HR-no-lesson-reveal`, `HR-no-here-opener`, `HR-no-inflation`, `HR-no-obvious`, `HR-no-slogans`, `HR-no-stock-phrasing`, `HR-no-reveal-formula`, `HR-no-autopilot-tricolon`)
- [ ] Every fact traced to the idea, the user's files or the user; anything else marked `[CHECK: ...]` (`HR-never-invent`, `HR-mark-unknowns`)
- [ ] Confidentiality notes respected in the text, the image and the alt text (`HR-confidentiality`)
- [ ] Nothing lifted from an inspiration post; any technique borrowed is named to the user in the review
- [ ] Length, hashtags and emoji match the user's samples, and any word limit in `{writing_overrides}` applies: count the words with a script (`wc -w`), never by eye
- [ ] Image chosen or briefed, with alt text
