# Review rubric

What the AI reviewer (`scripts/ai_review.py`) looks for: the faults the house rules name that a regex cannot see. What `test_check_text.py` already catches is listed under "Caught by test_check_text.py" below, and the reviewer does not repeat it. Where the script matches only some forms of a rule, the criterion lists the forms it misses under "Script misses". Word limits stay with the script: they are counted, never judged.

Each criterion has an ID the reviewer must use, and the house rules it enforces. The reviewer quotes the exact words for every finding; a finding whose quote is not in the text is dropped. When in doubt, it does not flag: a false alarm costs the user more than a missed one, because `test_check_text.py`, the self-check and the user's own read still follow.

The reviewer is calibrated on the user's corrections in `tests/feedback/cases.json`: every `review` case must be flagged with its criterion, and every `pass` case must pass (`python3 scripts/test_calibrate_reviewer.py`). Change this file only with the user's yes, and recalibrate after every change to it or to the model.

## Caught by test_check_text.py

Out of scope for the reviewer. Each example in backticks fails `test_check_text.py`, and `tests/test_ai_review.py` checks that it still does.

- Em and en dashes: `One idea — and another.`, `A range 1–2.`
- Banned phrases, the list in banned-phrases.txt: `Let's dive in.`
- Negative parallelism with "not" spelled out, in one sentence or two, and its fixed phrases: `It's not a tool, it's a habit.`, `It's not a tool. It's a habit.`, `It isn't just a tool.`, `Not because it was cheap, but because it was there.`, `Less talk, more action.`, `A habit, not just a tool.`
- Lesson-reveal framing with "taught", "learnt" or "learned": `What building it taught me`, `## What I learnt`, `## Lessons I learned`
- Number-pair slogans, as two counted nouns joined by a comma, or a heading that opens with a counted noun and a comma: `1 folder, 3 commands`, `## One ask, the week files itself`
- Titles and headings that start with "I" or "We": `# I built a thing`, `## We tried three tools`
- Montages of sentence fragments: `The strategy deck. The reason we picked vendor B. The goal we agreed on in January.`
- Staccato runs of short sentences: `You read it. You fix what it got wrong. You say yes.`
- Sentences that start with "Here is", "Here's" or "Here are": `Here's the plan.`
- AI-writing-pattern rules (house rules, section 2.2), the forms that are wrong on their own, each failing with the ID of its rule: `It plays a pivotal role in the team.`, `The note serves as a record.`, `Experts argue that agents need permissions.`, `Not only fast, but also private.`, `We utilize a vault.`, `In conclusion, it works.`, `It is important to note that the vault is private.`, `I hope this helps!`, `[Company Name] hired me.`, `## Conclusion`, `Edge-case notes, highlighting the need for review.`, `The valley is nestled in the heart of the city.`, `We prioritize practical, steady work to foster trust.`
- Word limits, counted per channel.

## Criteria

### `flourish`: drama for an ordinary problem
Rules: `HR-no-cinematic-openings`, `HR-no-inflation`.
A storytelling flourish that dramatizes something ordinary ("quietly stopped talking about in March", "the head of someone who left last spring"), or a claim made to sound bigger, more profound or more important than it is ("rules that matter enormously", "for the first time"). One short fragment as a second beat after a full sentence is the user's own style and is fine.

### `explaining-down`: writing below a tech-savvy reader
Rules: `HR-no-explaining-down`, `HR-metaphor-earns-place`, `HR-precise-jargon`.
An analogy standing in for a term the reader already knows (an agent as "a very diligent chief of staff", access layers as "three floors of a building"), a definition of a common term, or reassurance that no technical skill is needed. A metaphor that shows a property or a failure mode the term does not is fine.

### `selling`: a pitch where the piece should share knowledge
Rules: `HR-describe-not-sell`, `HR-close-reference-question`, `HR-no-launch-register`.
A promised outcome that was not measured ("nobody spends Monday chasing status", a tagline that promises a result instead of naming the mechanism), a sales adjective, a call to try, adopt, sign up or buy ("Try it, break it, tell me what's missing" as a close), urgency, or launch register. A close that shares a link, asks peers a real question or asks for feedback on open work is fine.

### `negative-parallelism`: a contrast formula the script misses
Rules: `HR-no-negative-parallelism`.
Defining something by what it is not, in a form `test_check_text.py` does not match: the "isn't" or "aren't" contraction, in one sentence or two, a "From X to Y" headline, "less about X and more about Y", "never X; it was Y", "not X but Y", "X rather than Y" used as a reveal. Say what the thing is. A plain comparison with a real alternative ("we chose Drive over git for notes, because...") is fine.
Script misses: `This isn't a tool. It's a habit.`, `It isn't a tool, it's a habit.`, `They aren't notes. They are decisions.`, `## From personal notes to company memory`, `It is less about the tooling and more about the ownership.`, `The point was never the model; it was the context.`

### `lesson-reveal`: a lesson announced instead of given
Rules: `HR-no-lesson-reveal`.
A title, heading or sentence that frames the author's lesson as a reveal, in a form `test_check_text.py` does not match. Give the lesson itself, in the reader's terms. A heading that states the point ("AI system design is organizational design") is fine.
Script misses: `## Five things I took away from building it`, `## My biggest takeaways`, `## What this project revealed about alignment`, `Building it showed me something about teams.`

### `slogan`: a tagline where a sentence belongs
Rules: `HR-no-slogans`.
Matched short fragments or clauses that read like a tagline, including a number pair in body text, in a form `test_check_text.py` does not fail (fragment pairs only get a warning there), in the text, a heading, image copy or alt text. Write the idea as an ordinary sentence. One short fragment as a second beat after a full sentence is the user's own style and is fine ("At least for now.").
Script misses: `Private by default. Shared on purpose.`, `Plain words. Real results.`, `Ship small, learn fast.`, `## Built to share, designed to protect`, `One ask on Friday, the week files itself.`

### `obvious`: a sentence the reader already knows
Rules: `HR-no-obvious`.
A statement a person working in tech would answer with "yes, obviously" ("every new chat starts from zero", "AI can make mistakes", "tools will keep changing").

### `false-link`: a connection the text does not support
Rules: `HR-concrete`, `HR-checkable-claims`.
A connective ("so", "because", "that's why", "which means") that joins two claims as cause and effect when the text does not show the link, or two separate problems presented as one.

### `unchecked-claim`: a claim about the world taken on trust
Rules: `HR-fact-check-user`, `HR-checkable-claims`, `HR-never-invent`.
A claim about tools, the industry or how a system works, stated as fact with nothing in the text to support it, often the user's own point written up as given ("that is why so many tech companies are focused on infrastructure"). The user's opinion is fine when it reads as their view.

### `generic-claim`: a generic claim where a fact belongs
Rules: `HR-ai-keep-specific-fact`, `HR-ai-no-significance-claims`, `HR-ai-no-coverage-padding`, `HR-ai-name-sources`.
A specific fact swapped for a claim that sounds important and could be about anything: a detail made to stand for a bigger movement, a subject praised as foundational without a fact, importance shown by who covered it, a view credited to unnamed experts or critics, in a form the stock phrases in `test_check_text.py` do not match. The fix is the fact itself, or cutting the sentence.
Script misses: `The repo reflects a growing movement towards shared context across the industry.`, `It became a cornerstone of how the team works.`, `The tool was written by a well-known engineer and widely discussed online.`

### `unasked-contrast`: a correction nobody asked for
Rules: `HR-ai-no-unasked-contrast`.
A contrast that corrects a view the reader does not hold, spread over two sentences or worded without "not": a "known for A... however, its real value lay in B" turn, a "was seen as X, but is really Y" reveal. A comparison with a real alternative the reader would weigh is fine.
Script misses: `The tool was known for speed. Its real value, however, lay in keeping notes consistent.`, `Early users saw it as a search tool. Over time it became the place where decisions are recorded.`

### `topic-definition`: a topic defined as if it were a proper noun
Rules: `HR-ai-no-topic-definition`.
An opening sentence that defines a generic topic, section or list title as a thing ("The skills list is a collection of..."). Say what the thing does.
Script misses: `The skills list is a collection of the commands the assistant can run.`, `The layers section is an overview of who sees what.`

### `repeated-idea`: one idea said in several places
Rules: `HR-no-repeated-idea`.
The same point made in two or more sections (the thesis in the hook, the reframe and the close; the layers in the overview and again in their own section), or a paragraph that restates the one before it in other words. The thesis may return once, as the takeaway. The reviewer quotes both places.
Script misses: restatements that share few words.

### `trivial-detail`: ordinary behaviour spelled out
Rules: `HR-detail-budget`, `HR-no-obvious`.
A sentence that describes what any tool of its kind does, or reference material the repo already holds (a list of commands, hooks or connectors; a step-by-step of routine behaviour), where a tech-savvy reader would learn nothing they could not guess. A design decision with its reason is fine.

### `chat-residue`: the assistant's voice left in the copy
Rules: `HR-ai-no-chat-residue`, `HR-ai-no-gap-hedging`, `HR-ai-no-corrective-framing`.
A hedge about missing information or what is "likely", an instruction to the writer, a conversational aside or a warning nobody asked for, in a form the stock phrases do not match. The gap belongs in a `[CHECK: ...]` marker and in the summary to the user.
Script misses: `The exact numbers are hard to pin down, so the figure is likely a few dozen.`, `Details on the pricing are hard to find.`

### `not-the-voice`: does not sound like the user
Rules: `HR-voice-posts`.
Only when voice samples are given. A post or article that reads like a CV, a corporate page or a generic LinkedIn post rather than the samples: CV verbs, credentials in passing, a register the samples never use.

## Scoring

Every draft gets an AI-pattern score from 0 to 100 (`scripts/ai_patterns.py`, shown by `scripts/test_check_text.py`), so a draft that trips no single rule can still fail for the number of soft signs it carries. The score starts at 100 and loses points per rule, never per word, so one repeated phrase cannot sink a piece on its own:

| Item | First hit of a rule | Each further hit | Cap per rule |
|---|---|---|---|
| Error (wrong on its own) | 12 | 4 | 30 |
| Warning (wrong in a cluster) | 4 | 2 | 12 |
| Reviewer finding | 10 | 10 | none |

Bands: pass from 85, review from 70 to 84 (read every warning and fix or keep it deliberately), fail below 70. Any error fails the draft whatever the score. The reviewer's findings are added to the score when `scripts/ai_review.py` runs, so the number in its report and the number in `test_check_text.py` use one scale. `tests/test_ai_patterns.py` holds this table to the code.
