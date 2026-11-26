# Post type: leaving a job

**Goal:** the user's network and potential recruiters see what the user did, the scale they worked at and how they think.
**Use it when:** the post's news is that the user is leaving an employer or has just left one: a resignation, the end of a contract or a long engagement, a layoff, a move to another company, a break.
**Not for:** a post about a new role that says nothing about the one before it, or a move to another team at the same employer.
**Word cap:** at most 100 words, hook to close, with no minimum. This is the length exception (see "Where it differs").
**Template:** `system/20-linkedin-posts/templates/post-leaving-a-job.md`, copied as `draft.md`.

Each section opens with where it comes from. *From the source* marks what the reel's caption says, restated here; the caption's own words are in quotation marks. *From the user* marks what the user set for this type on 23 November 2026: its goal, the rule for each line and the example sentences in the table under "Shape". *This repo* marks what was added here, at the points where a wrong step costs the user something and neither of them says anything.

## Source

*From the source and the user.* The Instagram account `the_elite_recruiter`, reel https://www.instagram.com/reel/DfxzqVtHB__/, read on 23 November 2026. Only the caption could be read as text; the audio was not available. Nothing below is credited to the caption beyond these points, in the caption's order:

1. A long farewell post, around 400 words, gets little reading, which wastes a good moment.
2. Leave out the stock opener: a count of years called incredible, then a difficult decision to close a chapter. Recruiters and hiring managers skim, and they look for facts more than for a personal story.
3. The format that works has four lines:
   - "What you did. One sentence with a metric."
   - "What you learned. One sentence, make it specific."
   - "What's next. One sentence, be confident."
   - "How people can stay connected. One line."
4. That format is clean and specific, and it shows the market quickly what the person can do.
5. Thank the people who mattered in private, and on LinkedIn "give them the receipts". The caption does not say what the receipts are; this repo's reading is under "Thanks".
6. The rest of the caption promotes the account and carries hashtags. It gives no example sentences and no advice on tagging, photos, hashtags or timing.

On 23 November 2026 the user set the goal, a rule for each of the four lines and an example sentence for lines 1 to 3. Where the user's rule and the caption differ (line 1 may run to two sentences), the user's rule wins.

## Before drafting

*This repo.* Settle these with the user in one batch, together with the questions of Step 2 (Frame):

1. **Is the departure public and agreed?** The employer and the team know, and any announcement the employer makes goes out first.
2. **From which date may the post go live?** The session never posts. The draft carries the date as `[CHECK: go-live date]` until the user confirms it, and the piece stays in `review` until then (`HR-mark-unknowns`).
3. **What may be said** about the reason for leaving and about the next step: all of it, the bare fact, or nothing.
4. **Which case of "What's next"** applies (the table under "Line 3").
5. **Which metric may be shared, and in what form:** the figures themselves, or the change in relative terms (see "The metric").

A missing answer does not hold up the draft. Draft from what `{profile}`, `{cv_master}` and `{portfolio_stories}` give, put a `[CHECK: ...]` where each answer belongs, and list every open marker in the summary (Step 6). Never fill a gap with something plausible (`HR-never-invent`, `HR-mark-unknowns`).

## Gather

*This repo.* Step 1 of the workflow, with these sources:

| For | Where it comes from |
|---|---|
| What you did, its scale and its metric | `{cv_master}` (the role being left: its bullets and their figures) and `{portfolio_stories}`. A figure already published on the user's own site (`links.portfolio_site` in `config.yaml`) counts too. |
| What you learned | `{portfolio_stories}` and the user's own words. A story that names a decision and what came of it is the best source. |
| What's next | The user, and `{profile}` once it is updated. |
| Confidentiality | The notes in `{profile}` and `{rules}`, which hold in full: no client of the employer, no internal project name, no figure they do not clear (`HR-confidentiality`). |

Every fact goes into `evidence.md` with its source. Each number the post writes in digits (the metric's figures and the time in the role) has to be in a row of that ledger, or `scripts/test_check_structure.py` fails the piece on `trace`.

## Reader

*From the user and this repo.* The goal names two readers, and the brief carries both. Who: the user's network (peers in their field, former colleagues, people who know the work) and potential recruiters and hiring managers, who skim. Their question: what did this person do, at what scale, and how do they think? The takeaway is the goal line, plus where the user goes next, and the level of detail is the four lines.

The second reader changes who the post is for. How it sounds stays the same: the register of the house rules, section 3, a practitioner telling peers plainly what they did, with no CV verbs and no pitch (`HR-voice-posts`).

## Shape: the four lines

*From the source and the user.* Four parts in this order, each one line and its own paragraph. They replace the arc in Step 3.

| Line | What it shows the reader | The rule | The user's example |
|---|---|---|---|
| 1. What you did | What the user did, and the scale they worked at | One or two sentences, with a metric | "I spent the last [number] years growing the digital business for a global consumer products company. We grew the revenue from [X] million to [Y] million." |
| 2. What you learned | How the user thinks | One sentence | "Biggest lesson: transformation moved at the speed of leadership alignment." |
| 3. What's next | Where the user goes from here | One sentence, said with confidence | "Next up I am joining [new employer] to lead digital and growth." |
| 4. How to stay connected | How to reach the user | One line | None given; this repo's example is under "Line 4". |

The sections below say how this repo writes each line.

### Line 1: what you did

*From the user, with this repo's way of writing it.* This line is the hook and the post's one real detail (Step 1 of the workflow). It says what the user worked on in plain verbs (grew, built, ran, rebuilt, wrote), never in CV verbs (`HR-voice-posts`), and it gives the metric.

Past tense carries the news: "I spent the last [number] years" tells the reader the role has ended, so the post needs no sentence announcing the departure. A user who is still in the role names the last day. Example: "Friday is my last day at [employer], where I spent [number] years rebuilding the onboarding flow."

The scale shows in two places: what the business is, in a few words ("a global consumer products company"), and the size of the metric. Name the employer or describe it, whichever tells the reader more and the user is free to say. The time in the role may be given once, with the work, as in the user's example.

The whole line fits in about 200 characters, which is what shows before "...see more" (post rules, section 3), so the reader gets the metric without a click. The stock opener, a job title first, years of experience offered as a credential, team size and budget all stay out (post rules, section 1).

### The metric

*From the user ("give a metric"), with this repo's rules for it.* The post carries one metric, in line 1. The only other number it may hold is the time in the role, also in line 1.

- One metric is one result of the user's own work. It may be written as a before and after pair, as in the user's example, when the pair is what shows the scale. A second result is a second metric and stays out.
- It is real and the user's to share: from `{cv_master}` or the user's site, where it is already cleared for outside readers. Any other figure, from memory or an internal dashboard, goes in as `[CHECK: may this figure be shared publicly?]` until the user says yes (`HR-mark-unknowns`).
- A confidentiality note decides the form. Where a note in `{profile}` or `{rules}` rules out an employer's absolute figures, write the change in relative terms (a percentage or a multiple) and the scale in words. The note outranks the example's wording (`HR-confidentiality`).
- With no figure the user may share, line 1 names the concrete result without one, and the summary says so. A figure is never invented or rounded up (`HR-never-invent`).
- Team size, budget and counts of launches or promotions stay out: they are the credentials the post rules keep out of a post.

### Line 2: what you learned

*From the user, with this repo's way of writing it.* This line shows how the user thinks. It states the lesson itself in one sentence: a claim about how the work really goes, which the user holds because of what happened in this role. In the user's example, the claim is that a transformation goes as fast as its leaders agree.

Make it a claim a peer could disagree with. A truth every reader already holds, such as good teams being worth a lot, shows nothing about the user (`HR-no-obvious`), so name what set the pace or made the difference. Inflated significance and a second lesson stay out (`HR-no-inflation`).

The line may open with a label of two or three words, as the user's example does ("Biggest lesson:"), when the lesson follows in the same sentence. The frames that promise a lesson and give it later stay out: `HR-no-lesson-reveal` lists them, and the checker fails them.

### Line 3: what's next

*From the user and the source, with this repo's four cases.* One sentence for the case that applies, as a plain statement of fact. Confident means no hedge ("hopefully", "we'll see"), no excitement words and no teaser (`HR-no-launch-register`). The line asks the reader nothing, since line 4 is the close.

| Case | How line 3 reads | Watch for |
|---|---|---|
| The next step is public | The user's example: "Next up I am joining [new employer] to lead digital and growth." | Tag the new employer only when the user wants it tagged. |
| It exists but cannot be named yet | Example: "In [month] I start a [kind of role] role, and I'll say where once it is announced." | Say the kind of work. No teaser such as "big news soon". |
| Open to roles | Example: "I'm looking for a [role] role on [kind of team or product], in [place] or remote." | Name exactly what kind of role; a line that says only "new opportunities" tells the reader nothing. |
| A break | Example: "I'm taking [the spring] off before my next role." | No apology, and no reason unless the user wants one. A length in months would be a number outside line 1. |

### Line 4: how to stay connected

*From the source, with this repo's way of writing it.* One line, and the post's only close: an offer to keep in touch. It names a channel that still works after the last day (messages on LinkedIn, the user's site) and, where it helps, the topic. Example: "If you work on onboarding or billing, message me here." A stock sign-off with an exclamation mark, a question, a request for likes or shares and the work email all stay out.

### Length

*This repo, for the four lines.* At most 100 words, hook to close, counted by the script. The user's three examples with a fourth line come to 57 words, and test posts written for this type with invented content came to 61 to 72 words; 100 leaves room for a long employer name or role title and rules out the long farewell the source warns about.

The type has no minimum: for its posts, the cap replaces the post rules' default length and any minimum in the user's voice guide (the last row under "Where it differs"). A lower cap in the user's own writing rules (`{writing_overrides}`) or the voice guide still applies.

## Where it differs

*From the user and this repo.* The rules for this type differ from the rules above it at these points, for this type's posts only (`post-types/README.md`, "Where a type's rules sit"). Everything else in those rules holds, and so does every error the checker reports.

| The rule above | In this type | Set by |
|---|---|---|
| The reader is a peer, and a post never lists achievements to a recruiter (post rules, section 1) | The readers are the user's network and potential recruiters. The post still reads as a practitioner telling peers what they did. | the user |
| At most one number (post rules, section 1; `HR-voice-posts`) | One metric, which may be a before and after pair, and the time in the role. Both sit in line 1. | the user |
| Never open with years of experience (post rules, section 1) | Line 1 may give the time in the role, with the work. Years of experience as a credential stay out. | the user |
| No lesson framing (post rules, section 2; `HR-no-lesson-reveal`) | Line 2 may open with a short label when the lesson follows in the same sentence. The frames the checker fails stay out. | the user |
| 120 to 250 words by default (post rules, section 3) | At most 100 words, with no minimum. | this repo, from the source's four lines |

A voice guide that keeps recruiters out of the reader, or years out of a post, gives way at the same points. The user's own writing rules (`{writing_overrides}`) do not: where they set a rule on one of them, that rule applies. When the draft is shown, the summary names each row the post uses, so the user can still say no.

## Leaving without choosing to

*This repo.* A layoff, a role cut or a contract that was not renewed takes the same four lines. The reason stays out unless the user wants it in, and then it is one plain clause ("my role was cut in the [month] reorganisation"). The post never criticises the employer or the people who decided. Line 3 is usually "open to roles" or "a break", stated just as plainly.

## What stays out

*From the source and this repo.*

- The stock opener (*from the source*): an opening that calls the years incredible and announces a difficult decision to close a chapter. The post opens with line 1.
- A list of thanks or of tagged names (*this repo*, from the source's advice to thank people in private). Tag the new employer only when the user wants it, and a colleague only at that colleague's request.
- A second metric, and any number outside line 1.
- The reason for leaving, unless the user wants it in, and any criticism of the employer (*this repo*).
- Hashtags beyond what the post rules allow: none, or up to three when the user's own posts use them.
- Anything under a confidentiality note (`HR-confidentiality`).

## Thanks

*From the source, with this repo's reading.* The source says to thank people in private and to "give them the receipts" on LinkedIn, without saying what the receipts are. This repo reads it this way: each person gets the thanks by private message, and the public post carries the proof, meaning what the work produced, which lines 1 and 2 already hold.

- Offer to draft the private messages with `/write-text`, one per person, from what the user says each one did. Never draft them by default.
- A LinkedIn recommendation for a colleague is a public way to credit one person's work. `/write-text` drafts that too, on request only.
- The post itself does not name anyone to thank.

## Image

*This repo.* Step 4 of the workflow holds: one image, the user's own photo first, alt text always. For this type:

- A photo with other people in it (a team photo, a last-day photo) goes up only once each person in it has agreed. The draft carries `[CHECK: everyone in the photo agreed]` until then (`HR-mark-unknowns`).
- Screens, whiteboards, documents, badges and anything showing a client's or a project's name stay out of the frame, or are cropped out (`HR-confidentiality`).
- A screenshot of the work only when the work is public: a live page, a public repo.

## Check

*This repo.* Step 5 of the workflow, with this type's cap:

```bash
python3 scripts/test_check_text.py workspace/pieces/<piece>/draft.md --max-words 100 --visuals workspace/pieces/<piece>/visuals.md --channel 'LinkedIn post'
python3 scripts/test_check_structure.py workspace/pieces/<piece> --channel 'LinkedIn post'
```

The first counts the `## Post` section and runs the house rules; the second traces every number in the post to `evidence.md`. Over 100 words, shorten lines 1 and 2 first and never cut line 4. Then the self-check in `{social_voice_rules}`, section 6, read with the table under "Where it differs", and this one, for what the scripts cannot see:

- [ ] Four lines in the order of the table, each its own paragraph: line 1 in one or two sentences, lines 2 and 3 in one sentence each, line 4 in one line and the only close
- [ ] Line 1 shows the work and its scale, with one metric that is the user's to share, in the form the confidentiality notes allow (no metric only when the user has none to share)
- [ ] No number outside line 1, and in line 1 only the metric and the time in the role
- [ ] No stock opener: no incredible years, no difficult decision, no chapter closing, no title or years of experience as a credential
- [ ] Line 2 states the lesson itself, as a claim a peer could disagree with, with no frame that promises a lesson
- [ ] Line 3 is one of the four cases, said plainly, with no hedge and no teaser
- [ ] No list of thanks, no tagged colleague, no criticism of the employer, no reason the user did not ask for
- [ ] The go-live date, and what may be said about the reason and the next step, confirmed by the user or still marked `[CHECK]`
- [ ] Everyone in the photo agreed, and no screen or whiteboard is in the frame
- [ ] The summary names each row of "Where it differs" that the post uses

## After it is live

*This repo.* Step 6 of the workflow as usual, `/add-voice-sample mine` included. Leaving a job also changes the profile, the master CV and the user's LinkedIn profile. Offer the profile repo's skills that own the first two: `/add-new-job` once the next role starts (it ends the old role in the master CV and updates the profile); until then `/update-profile` for the profile and `/update-cv-master` for the master CV. The LinkedIn profile itself (the headline, the role's end date) is the user's to change on LinkedIn. Never edit any of them from here.
