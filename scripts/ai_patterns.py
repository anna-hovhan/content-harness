#!/usr/bin/env python3
"""The AI-writing-pattern rules (house-rules.md, section 2.2): detectors, coverage map and score.

test_check_text.py calls scan() on every draft. Each hit names the rule it breaks (an HR-ai- ID) and has a severity:

  error     a pattern that is wrong on its own: it fails the check
  warning   a pattern that is wrong in a cluster: it is read, and it costs points in the score

score() turns the hits (and, when the AI reviewer ran, its findings) into a number from 0 to 100, with the
weights and bands the scoring section of system/00-core/test_review-rubric.md documents; tests/test_ai_patterns.py
holds the two together. A score under FAIL_BELOW fails the check even when no single hit is an error.

COVERAGE says how each 2.2 rule is evaluated: "scan" (this module), "reviewer" (a rubric criterion, for what a
pattern cannot see) or "commit" (the commit-message check in scripts/hooks/test_check_content.py). tests/test_ai_patterns.py
fails when a rule in house-rules.md has no entry here, or an entry has nothing behind it.

Standard library only. Lines inside code fences, inline code, HTML comments and the scaffold sections of a draft
("Check before posting") are not scanned.
"""
from __future__ import annotations

import re
import statistics

HARD, SOFT = "error", "warning"

# --- scoring (documented in test_review-rubric.md, "Scoring") -------------------------------------------------------
WEIGHTS = {  # severity: (first hit of a rule, each further hit, cap per rule)
    HARD: (12, 4, 30),
    SOFT: (4, 2, 12),
}
FINDING_COST = 10  # an AI reviewer finding
PASS_FROM, FAIL_BELOW = 85, 70

# --- how each rule is evaluated ----------------------------------------------------------------------------------
COVERAGE: dict[str, tuple[str, ...]] = {
    "HR-ai-keep-specific-fact": ("reviewer",),
    "HR-ai-no-significance-claims": ("scan", "reviewer"),
    "HR-ai-no-coverage-padding": ("scan", "reviewer"),
    "HR-ai-state-the-fact": ("scan",),
    "HR-ai-no-trailing-ing": ("scan",),
    "HR-ai-name-the-relationship": ("scan",),
    "HR-ai-name-sources": ("scan", "reviewer"),
    "HR-ai-no-challenges-formula": ("scan",),
    "HR-ai-plain-headings": ("scan",),
    "HR-ai-vocabulary-density": ("scan",),
    "HR-ai-plain-copulas": ("scan",),
    "HR-ai-no-unasked-contrast": ("scan", "reviewer"),
    "HR-ai-no-topic-definition": ("reviewer",),
    "HR-ai-plain-verbs": ("scan",),
    "HR-ai-no-holds": ("scan",),
    "HR-ai-no-repeated-list-opener": ("scan",),
    "HR-ai-varied-rhythm": ("scan",),
    "HR-ai-no-brochure-tone": ("scan",),
    "HR-ai-no-wrap-up": ("scan",),
    "HR-ai-no-abrupt-end": ("scan",),
    "HR-ai-prose-default": ("scan",),
    "HR-ai-heading-levels": ("scan",),
    "HR-ai-no-emoji-markers": ("scan",),
    "HR-ai-straight-quotes": ("scan",),
    "HR-ai-no-chat-residue": ("scan", "reviewer"),
    "HR-ai-no-gap-hedging": ("scan", "reviewer"),
    "HR-ai-no-corrective-framing": ("scan", "reviewer"),
    "HR-ai-no-template-blanks": ("scan",),
    "HR-ai-channel-markup": ("scan",),
    "HR-ai-no-artefacts": ("scan",),
    "HR-ai-specific-change-notes": ("commit",),
    "HR-ai-no-service-register": ("scan", "commit"),
}
# Rules of section 2.1 or 3 that this module also checks (a pattern the older rules state but nothing enforced).
OTHER_RULES_CHECKED = {"HR-short-paragraphs", "HR-no-sweeping-words"}


def _c(*patterns: str) -> list[re.Pattern]:
    return [re.compile(p, re.I) for p in patterns]


_START = r"(?:^\s*|[.!?]\s+)"  # the start of a sentence

# Building blocks for the "holds" checks (HR-ai-no-holds).
_ADV = r"(?:still\s+|also\s+|only\s+|now\s+|no\s+longer\s+|really\s+)?"
_HOLD_AFTER = (r"(?:when|once|if|only\s+(?:when|if|once)|as\s+long\s+as|until|unless|depends|true|whatever"
               r"|in\s+(?:production|practice)|for\s+(?:every|all|everything|both))\b")
_RULE_NOUN = r"(?:rules?|claims?|checks?|guards?|assumptions?|promises?|arguments?|principles?|results?)"
_UP_AFTER = (r"(?=\s*(?:[.,;:!?)]|$)|\s+(?:in\s+(?:production|practice|use)|under|over\s+time|well|when|once|if|as"
             r"|for\s+(?:long|now|a\s+(?:day|week|month|year|while))|only|against)\b)")

# (rule, severity, label, patterns)
PHRASE_CHECKS: list[tuple[str, str, str, list[re.Pattern]]] = [
    ("HR-ai-no-significance-claims", HARD, "significance claim", _c(
        r"\b(?:is|was|are|were)\s+(?:a|an)\s+(?:testament|reminder)\b",
        r"\bplay(?:s|ed|ing)?\s+an?\s+(?:crucial|pivotal|vital|key|significant)\s+role\b",
        r"\ba\s+(?:crucial|pivotal|vital)\s+(?:role|moment)\b",
        r"\bunderscor(?:es|ed|ing)\s+(?:the|its|their|a|an|how|that|why)\b",
        r"\bhighlights?\s+(?:its|the|their)\s+(?:importance|significance)\b",
        r"\bevolving\s+landscape\b", r"\bindelible\s+mark\b", r"\bfocal\s+point\b",
        r"\bsetting\s+the\s+stage\s+for\b", r"\b(?:key|major)\s+turning\s+point\b",
        r"\bdeeply\s+rooted\b", r"\b(?:marks|represents)\s+an?\s+(?:significant\s+|major\s+)?shift\b",
        r"\breflects?\s+(?:a\s+)?broader\b", r"\b(?:this|that|it|which)\s+matters\s+because\b",
        r"\bleaving\s+an?\s+(?:lasting|indelible)\s+(?:mark|impact)\b")),
    ("HR-ai-no-coverage-padding", HARD, "importance shown by coverage", _c(
        r"\bindependent\s+coverage\b", r"\b(?:local|regional|national|major)\s+(?:media\s+)?(?:outlets?|publications?)\b",
        r"\b(?:business|tech|trade|music|industry)\s+(?:outlets?|publications?)\b",
        r"\bactive\s+(?:social\s+media|digital|online)\s+presence\b",
        r"\bmaintains\s+an?\s+(?:active|strong)\s+(?:\w+\s+){1,2}presence\b",
        r"\bwritten\s+by\s+a\s+leading\s+expert\b")),
    ("HR-ai-state-the-fact", SOFT, "a record 'identifies' the fact", _c(
        r"\b(?:records?|listings?|filings?|profiles?|website|readme|pages?)\s+(?:identif(?:y|ies)|lists?)\b",
        r"\bwas\s+identified\s+(?:by\s+[^,.]{1,40}\s+)?as\b", r"\b(?:is|are)\s+listed\s+(?:in|on|as)\b")),
    ("HR-ai-no-trailing-ing", HARD, "trailing comment clause", _c(
        r",\s+(?:thereby\s+|thus\s+)?(?:highlighting|underscoring|emphasi[sz]ing|reflecting|symboli[sz]ing|"
        r"contributing\s+to|cultivating|fostering|showcasing|solidifying|cementing)\b")),
    ("HR-ai-no-trailing-ing", SOFT, "trailing comment clause", _c(
        r",\s+(?:thereby\s+|thus\s+)?(?:ensuring|enhancing|encompassing)\b", r"\bvaluable\s+insights?\b",
        r",\s+(?:aligning|resonating)\s+with\b")),
    ("HR-ai-name-the-relationship", SOFT, "vague connection", _c(
        r"\bin\s+(?:connection|association)\s+with\b", r"\b(?:widely|particularly)\s+associated\s+with\b",
        r"\b(?:was|were|is|are)\s+associated\s+with\b", r"\bconnected\s+with\b")),
    ("HR-ai-name-sources", HARD, "unnamed source", _c(
        r"\b(?:experts|observers|critics|analysts)\s+(?:argue|say|believe|note|suggest|have\s+(?:noted|cited|pointed))\b",
        r"\bsome\s+(?:critics|experts|observers)\b", r"\bindustry\s+(?:reports|observers|insiders)\b",
        r"\bseveral\s+(?:sources|publications|outlets)\b")),
    ("HR-ai-no-challenges-formula", HARD, "challenges formula", _c(
        r"\bdespite\s+(?:its|these|the|such)\s+[^.]{0,60}?\b(?:faces?|continues\s+to\s+face)\s+"
        r"(?:several|some|many|a\s+number\s+of)\s+challenges\b",
        r"\bdespite\s+these\s+challenges\b")),
    ("HR-ai-plain-copulas", HARD, "inflated 'is'", _c(
        r"\b(?:serves|stands|served|stood)\s+as\b", r"\bboasts\b", r"\bholds\s+the\s+distinction\s+of\s+being\b")),
    ("HR-ai-plain-copulas", SOFT, "inflated 'is' or 'has'", _c(
        r"\b(?:functions|operates)\s+as\s+an?\b", r"\b(?:features|offers)\s+an?\b", r"\b(?:represents|marks)\s+an?\b",
        r"\bventured\s+into\b", r"\bbegan\s+(?:his|her|their|my)\s+career\s+as\b", _START + r"[A-Z][^.]{0,40}\brefers\s+to\b")),
    ("HR-ai-no-unasked-contrast", HARD, "contrast nobody asked for", _c(
        r"\bnot\s+only\b[^.?!]{1,100}?\bbut\s+also\b", r"\brather\s+than\s+(?:simply|just|merely)\b",
        r"\bno\s+\w+(?:\s+\w+)?,\s+no\s+\w+(?:\s+\w+)?,\s+(?:just|only)\b",
        r"\b(?:it|this|that)(?:['’]s|\s+is)\s+not\s+(?:just|only|merely)\b")),
    ("HR-ai-no-unasked-contrast", SOFT, "'rather than' contrast", _c(r"\brather\s+than\b")),
    ("HR-ai-plain-verbs", HARD, "stiff verb", _c(r"\butili[sz](?:e|es|ed|ing|ation)\b")),
    # "hold" for "work", "apply" or "be followed" (HR-ai-no-holds). An error only where the words around the verb show
    # it has no object, so "this file holds the text", "on hold", "press and hold for two seconds" and "was held up
    # by a late answer" pass. The forms these patterns miss are named in the rule and need a read.
    ("HR-ai-no-holds", HARD, "'holds' for 'works' or 'applies'", _c(
        # a subject, then "holds" and a word that cannot start an object: "it holds when", "which holds until"
        r"\b[\w'’-]+\s+" + _ADV + r"holds,?\s+" + _HOLD_AFTER,
        # the same for a plural subject: "the rules hold when", "they hold for every channel"
        r"\b(?:they|these|those|both|[\w'’-]+s)\s+(?:all\s+)?" + _ADV + r"(?:do\s+not\s+|don['’]t\s+)?hold,?\s+" + _HOLD_AFTER,
        # a rule-like subject and the end of the clause: "the rule holds.", "the claim does not hold."
        r"\b" + _RULE_NOUN + r"\s+(?:does\s+not\s+|doesn['’]t\s+|do\s+not\s+|don['’]t\s+|did\s+not\s+|didn['’]t\s+|will\s+not\s+|won['’]t\s+)?"
        + _ADV + r"holds?\s*(?=[.;:!?)]|$)",
        # "whether it holds", "if the rule holds", unless an object follows
        r"\b(?:whether|if)\s+(?:it|this|that|they|the\s+[\w'’-]+)\s+" + _ADV
        + r"holds?\b(?=\s*(?:[.,;:!?)]|$)|\s+(?:is|was|will|would|can|could|should|may|might|depends|matters|decides|when|once|if|until|unless|in|up|true|and|or|but)\b)",
        # "holds up", with nothing held up: "it holds up in production", "the rule held up for a month"
        r"\b(?:holds?|holding)\s+up\b" + _UP_AFTER,
        r"(?<!\bwas )(?<!\bwere )(?<!\bgot )(?<!\bbeen )(?<!\bbe )(?<!\bis )(?<!\bare )(?<!\bget )(?<!\bgets )(?<!\bbeing )\bheld\s+up\b" + _UP_AFTER,
        r"\b(?:holds?|held|holding)\s+true\b",
        # a rule-like subject in the past: "the rule held for a month", "the rules held when I tested them"
        r"\b" + _RULE_NOUN + r"\s+" + _ADV + r"held\b(?=\s*(?:[.,;:!?)]|$)|\s+(?:when|once|until|for|in|under)\b)")),
    # Forms that are often this verb and sometimes not: a warning to read. "Holds for", "holds in", and "lives" or
    # "sits" for where a thing is (people also live and sit somewhere, so only thing nouns count as the subject).
    ("HR-ai-no-holds", SOFT, "'holds', 'lives' or 'sits' where a plain verb says it", _c(
        r"\b[\w'’-]+\s+" + _ADV + r"holds,?\s+(?:only\s+)?(?:for(?!\s+(?:every|all|everything|both)\b)|under|across|while|in(?!\s+(?:production|practice)\b))\b",
        r"\b(?:they|these|those|both|[\w'’-]+s)\s+(?:all\s+)?" + _ADV + r"hold,?\s+(?:only\s+)?(?:for(?!\s+(?:every|all|everything|both)\b)|under|across|while|in(?!\s+(?:production|practice)\b))\b",
        r"\b(?:rules?|files?|copy|copies|checks?|guards?|logic|code|data|facts?|notes?|ideas?|voice|content|sections?|docs?)"
        r"\s+(?:now\s+|still\s+|all\s+|only\s+)?live[sd]?\s+(?:in|on|at|inside|under|with|there|here|elsewhere|next\s+to)\b",
        r"\b(?:rules?|files?|checks?|guards?|logic|code|data|pieces?|repos?|layers?|folders?)"
        r"\s+(?:now\s+|still\s+|all\s+|only\s+)?s(?:its?|at)\s+(?:in|on|at|behind|between|inside|outside|under|above|below|upstream|downstream|next\s+to|where|there|here)\b")),
    # Three or more list items in a row that open with the same possessive: "my writing, my job search, my images".
    # An item is one or two words, and a comma, a semicolon or "and" stands between items, so a sentence such as
    # "I told my manager, my manager told her team, and my team heard it last" is not read as a list.
    ("HR-ai-no-repeated-list-opener", HARD, "list that repeats its opening word", _c(
        r"\b(my|our|your|their|his|her|its)\s+[\w'’-]+(?:\s+[\w'’-]+)?[,;]\s+\1\s+[\w'’-]+(?:\s+[\w'’-]+)?(?:[,;]\s+(?:(?:and|or)\s+)?|\s+(?:and|or)\s+)\1\s+[\w'’-]+")),
    ("HR-ai-plain-verbs", SOFT, "stiff verb", _c(
        r"\bauthored\b", r"\brelocated\b", r"\bpassed\s+away\b", r"\bcommenced\b", r"\bendeavou?r(?:s|ed)?\b",
        r"\bfacilitat(?:e|es|ed|ing)\b")),
    # Sweeping words (HR-no-sweeping-words, house rules 2.1, set by the user on 2026-11-24): "nobody" and "no one" are
    # errors, since the user turned down "Nobody has mapped..." and "nobody wrote down". "Everyone" and "everybody" are
    # warnings to read: a bounded "everyone on the call" can be the specific claim the rule asks for, which a pattern
    # cannot tell from a sweeping one. "No one-off" and "no one-size-fits-all" are not "no one".
    ("HR-no-sweeping-words", HARD, "sweeping word", _c(r"\bnobody\b", r"\bno[\s-]one\b(?![-\w])")),
    ("HR-no-sweeping-words", SOFT, "sweeping word, state the specific claim if it is one", _c(r"\bevery(?:one|body)\b")),
    ("HR-ai-no-brochure-tone", HARD, "brochure tone", _c(
        r"\bnestled\b", r"\bin\s+the\s+heart\s+of\b", r"\bvibrant\b", r"\bgroundbreaking\b", r"\brenowned\b",
        r"\bdiverse\s+array\b", r"\brich\s+tapestry\b", r"\bnatural\s+beauty\b")),
    ("HR-ai-no-brochure-tone", SOFT, "brochure tone", _c(
        r"\bprofound(?:ly)?\b", r"\bshowcas(?:e|es|ed|ing)\b", r"\bexemplif(?:y|ies|ied)\b", r"\bcommitment\s+to\b")),
    ("HR-ai-no-wrap-up", HARD, "summary wrap-up", _c(
        _START + r"(?:in\s+(?:summary|conclusion)|to\s+sum\s+up|all\s+in\s+all)\b")),
    ("HR-ai-no-wrap-up", SOFT, "summary wrap-up", _c(_START + r"overall,")),
    ("HR-ai-no-chat-residue", HARD, "chatbot talk", _c(
        r"\bi\s+hope\s+(?:this|that)\s+(?:helps|clarifies)\b", r"\bof\s+course!", r"\bcertainly!", r"\bgreat\s+question\b",
        r"\byou['’]re\s+absolutely\s+right\b", r"\bwould\s+you\s+like\s+(?:me\s+)?to\b", r"\bis\s+there\s+anything\s+else\b",
        r"\blet\s+me\s+know\s+if\b", r"\ba\s+more\s+detailed\s+breakdown\b", r"\bas\s+an\s+ai\b",
        r"\bas\s+of\s+my\s+(?:last\s+)?knowledge\b", r"\bi['’]m\s+sorry,?\s+but\b",
        r"\bi\s+(?:cannot|can['’]t)\s+(?:offer|provide|give)\s+(?:medical|legal|financial)\b",
        r"\b(?:check|verify|confirm)\b[^.\n]{0,40}\bbefore\s+(?:publishing|submitting|posting)\b",
        r"\bbefore\s+(?:publishing|submitting|posting),?\s+(?:make\s+sure|check|verify)\b", r"\bLEAD:\s")),
    ("HR-ai-no-gap-hedging", HARD, "hedge about missing information", _c(
        r"\b(?:while\s+)?(?:specific\s+)?details\s+(?:are|remain)\s+(?:limited|scarce|unclear)\b",
        r"\bnot\s+widely\s+(?:available|documented|disclosed|known)\b",
        r"\bin\s+the\s+(?:provided|available)\s+(?:sources|search\s+results|information)\b",
        r"\bbased\s+on\s+(?:the\s+)?available\s+information\b", r"\bmaintains\s+a\s+low\s+profile\b",
        r"\bkeeps?\s+(?:his|her|their)\s+personal\s+(?:life|details)\s+private\b")),
    ("HR-ai-no-corrective-framing", HARD, "corrective framing", _c(
        r"\bshould\s+be\s+(?:treated|presented|viewed|read)\s+as\s+[^.]{0,60}?\brather\s+than\b",
        r"\bdoes\s+not\s+(?:by\s+itself|in\s+itself)\s+establish\b", r"\bit\s+is\s+important\s+to\s+(?:note|remember|recognize)\b",
        r"\bit['’]s\s+(?:important\s+to\s+note|worth\s+noting)\b")),
    ("HR-ai-no-corrective-framing", SOFT, "corrective framing", _c(
        r"\bshould\s+not\s+be\s+confused\s+with\b", r"\bthis\s+varies\s+by\s+jurisdiction\b")),
    ("HR-ai-no-template-blanks", HARD, "template blank", _c(
        r"\[(?:Name|Your\s+Name|Company(?:\s+Name)?|Year|Date|Founder\s+Names?|Entertainer['’]?s\s+Name|Insert[^\]]*|URL|Link)\]",
        r"\((?:add|insert)\s+your\s+[^)]{0,40}\)", r"\(\s*if\s+available\s*\)", r"\b20\d\d-XX-XX\b|\bXXXX-XX-XX\b",
        r"\bINSERT_[A-Z_]+\b", r"\bexample\.com/source\d*\b", r"\bExample\s+Source\s+Title\b",
        r"\bEvidence\s+to\s+be\s+supplied\b")),
    ("HR-ai-no-artefacts", HARD, "interface artefact", _c(
        r"contentReference\[oaicite", r"\boaicite\b", r"\bturn\d+(?:search|view)\d+\b", "↩",
        r"utm_source=(?:chatgpt\.com|openai|copilot\.com)", r"referrer=grok\.com")),
    ("HR-ai-no-service-register", HARD, "customer-service register", _c(
        r"\bi\s+apologi[sz]e\b", r"\bi\s+have\s+carefully\s+reviewed\b", r"\bany\s+inconvenience\b",
        r"\bplease\s+point\s+them\s+out\s+and\s+i\s+will\b")),
]

# Headings that are stock formulas, matched on the whole heading.
STOCK_HEADINGS = re.compile(
    r"^(?:awards\s+and\s+recognition|recognition|challenges\s+and\s+(?:legacy|future|opportunities)|future\s+outlook|"
    r"conclusion|in\s+conclusion|in\s+summary|final\s+thoughts|key\s+takeaways|about\s+me|my\s+interests|let['’]s\s+connect!?)$", re.I)

# Commit messages and change notes (HR-ai-specific-change-notes, HR-ai-no-service-register).
CHANGE_NOTE_PHRASES = [(rule, label, re.compile(p, re.I | re.M)) for rule, label, p in [
    ("HR-ai-specific-change-notes", "stacked compliance claim", r"\bensur(?:ed|ing)\b[^.\n]{0,40}\b(?:adheres?|compl(?:y|ies|iance))"),
    ("HR-ai-specific-change-notes", "stacked compliance claim", r"\badhere[sd]?\s+to\b"),
    ("HR-ai-specific-change-notes", "stock edit verb", r"\b(?:refined|enhanced|enriched|streamlined)\b"),
    ("HR-ai-specific-change-notes", "vague improvement", r"\bimprov(?:ed|es|ing)\s+(?:the\s+)?(?:clarity|flow|readability)\b|\bfor\s+clarity\s+and\s+flow\b"),
    ("HR-ai-specific-change-notes", "stock opener", r"^\s*(?:comprehensive|concise)\s+(?:rewrite|edit)\s*:"),
    ("HR-ai-specific-change-notes", "states the obvious", r"\baddressed\s+(?:the\s+)?(?:reviewer\s+|review\s+)?feedback\b"),
    ("HR-ai-specific-change-notes", "sourcing over substance", r"\badded\s+(?:sourced|verified)\s+(?:content|information)\b"),
    ("HR-ai-specific-change-notes", "what was not changed", r"\b(?:preserv(?:ed|ing)|retain(?:ed|ing))\s+(?:the\s+)?(?:existing|original)\b"),
    ("HR-ai-no-service-register", "customer-service register", r"\bi\s+apologi[sz]e\b|\bi\s+have\s+carefully\s+reviewed\b|\bany\s+inconvenience\b"),
]]

VOCAB = re.compile(
    r"\b(challeng(?:e|es|ed|ing)|clearer|dependable|echoed|foster(?:s|ed|ing)?|leverag(?:e|es|ed|ing)|matters|multifaceted|"
    r"practical|prioriti[sz](?:e|es|ed|ing)|quietly|steady|universally|underscor(?:e|es|ed|ing)|causal|empirical|"
    r"correlat(?:e|es|ed|ing))\b", re.I)
VOCAB_ERROR_DISTINCT, VOCAB_WARN_DISTINCT, VOCAB_DENSITY_PER_1000 = 3, 2, 8

HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
IMAGE_MARKER = re.compile(r"^\s*\[IMAGE\s+v\d+\s*:[^\]]*\]\s*$")
SCAFFOLD_HEADING = re.compile(r"^(?:check\s+before\s+(?:posting|publishing|sending)|open\s+markers|notes?\s+for\s+the\s+user)\b", re.I)
SMALL_WORDS = {"a", "an", "the", "and", "or", "but", "nor", "for", "of", "in", "on", "at", "to", "by", "with", "from",
               "as", "vs", "via", "is", "are", "into", "over", "per"}
EMOJI_START = re.compile("^[\U0001F300-\U0001FAFF☀-➿⭐⬆✅❌✨]")
CURLY = re.compile("[“”‘’]")
BOLD = re.compile(r"\*\*[^*\n]+\*\*")
LABEL_BULLET = re.compile(r"^\s*[-*]\s+\*\*[^*]+?\*\*\s*:?|^\s*[-*]\s+\*\*[^*]+?:\*\*")
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
WORD = re.compile(r"[A-Za-z0-9][\w'’-]*")
FLAT_MIN_SENTENCES, FLAT_SHARE, FLAT_STDEV = 12, 0.9, 3.8


def _hit(rule: str, severity: str, line: int, message: str) -> dict:
    return {"rule": rule, "severity": severity, "line": line, "message": f"{message} ({rule})"}


def prose_lines(text: str) -> list[tuple[int, str]]:
    """(line number, line) for every line the pattern checks read: code, comments and scaffold sections are left out,
    inline code is blanked."""
    out: list[tuple[int, str]] = []
    in_fence = in_comment = in_scaffold = False
    for n, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if in_comment:
            in_comment = "-->" not in raw
            continue
        if stripped.startswith("<!--"):
            in_comment = "-->" not in raw
            continue
        m = HEADING.match(raw)
        if m:
            in_scaffold = bool(SCAFFOLD_HEADING.match(m.group(2)))
        if in_scaffold:
            continue
        out.append((n, re.sub(r"`[^`\n]*`", lambda mm: " " * len(mm.group(0)), raw)))
    return out


def _paragraphs(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Prose paragraphs: runs of consecutive non-blank lines that are not headings, lists, tables, quotes or markers."""
    paras: list[tuple[int, list[str]]] = []
    current: list[str] = []
    start = 0
    for n, line in lines:
        prose = bool(line.strip()) and not HEADING.match(line) and not IMAGE_MARKER.match(line) \
            and not re.match(r"^\s*(?:[-*>|]|\d+\.)\s*", line) and not line.strip().startswith("[")
        if prose:
            if not current:
                start = n
            current.append(line.strip())
        elif current:
            paras.append((start, current))
            current = []
    if current:
        paras.append((start, current))
    return [(n, " ".join(p)) for n, p in paras]


def title_case(heading: str) -> bool:
    words = re.findall(r"[A-Za-z][A-Za-z'’-]*", heading)
    if len(words) < 4:
        return False
    content = [w for w in words[1:] if w.lower() not in SMALL_WORDS]
    if len(content) < 3:
        return False
    return sum(1 for w in content if w[0].isupper()) / len(content) >= 0.8


def _section_range(text: str, title: str) -> tuple[int, int] | None:
    """First and last line number of the body of a '## <title>' section."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines, 1):
        m = HEADING.match(line)
        if start is None:
            if m and len(m.group(1)) == 2 and m.group(2).strip().lower() == title.lower():
                start = i + 1
        elif m and len(m.group(1)) <= 2:
            return start, i - 1
    return (start, len(lines)) if start is not None else None


def scan(text: str, channel: str | None = None) -> list[dict]:
    """All pattern hits in the text, as dicts with rule, severity, line and message."""
    hits: list[dict] = []
    lines = prose_lines(text)
    channel = (channel or "").lower()

    if text.lstrip().startswith("```"):
        hits.append(_hit("HR-ai-channel-markup", HARD, 1, "the whole text is wrapped in a code block"))

    for n, line in lines:
        if IMAGE_MARKER.match(line):
            continue
        heading = HEADING.match(line)
        if heading and STOCK_HEADINGS.match(heading.group(2).strip()):
            hits.append(_hit("HR-ai-plain-headings", HARD, n, f"stock heading '{heading.group(2).strip()}'"))
        if heading and title_case(heading.group(2)):
            hits.append(_hit("HR-ai-plain-headings", SOFT, n, f"Title Case heading, use sentence case: '{heading.group(2).strip()}'"))
        for rule, severity, label, patterns in PHRASE_CHECKS:
            for pat in patterns:
                found = list(pat.finditer(line))
                for m in found:
                    hits.append(_hit(rule, severity, n, f"{label} '{m.group(0).strip()[:60]}'"))
                if found:
                    break  # one pattern per check and line: overlapping patterns must not count a phrase twice
        if EMOJI_START.match(re.sub(r"^\s*(?:#+\s+|[-*]\s+|\d+\.\s+)", "", line)) and (heading or re.match(r"^\s*(?:[-*]|\d+\.)\s", line)):
            hits.append(_hit("HR-ai-no-emoji-markers", SOFT, n, "emoji at the start of a heading or list item"))
        if CURLY.search(line):
            hits.append(_hit("HR-ai-straight-quotes", SOFT, n, "curly quotes or apostrophes"))

    # Vocabulary clusters, per paragraph and over the whole text.
    words = 0
    all_vocab = 0
    for n, para in _paragraphs(lines):
        words += len(WORD.findall(para))
        found = [m.group(1).lower()[:6] for m in VOCAB.finditer(para)]
        all_vocab += len(found)
        distinct = len(set(found))
        if distinct >= VOCAB_ERROR_DISTINCT:
            hits.append(_hit("HR-ai-vocabulary-density", HARD, n, f"cluster of AI vocabulary ({', '.join(sorted(set(found)))})"))
        elif distinct == VOCAB_WARN_DISTINCT:
            hits.append(_hit("HR-ai-vocabulary-density", SOFT, n, f"two AI-vocabulary words in one paragraph ({', '.join(sorted(set(found)))})"))
    if words >= 200 and all_vocab * 1000 / words > VOCAB_DENSITY_PER_1000:
        hits.append(_hit("HR-ai-vocabulary-density", SOFT, 1, f"{all_vocab} AI-vocabulary words in {words} words"))

    # Bold: at most one phrase per paragraph (HR-short-paragraphs).
    for n, line in lines:
        if line.lstrip().startswith(("|", "-", "*", "#")) or re.match(r"^\s*\d+\.", line):
            continue
        if len(BOLD.findall(line)) > 1:
            hits.append(_hit("HR-short-paragraphs", SOFT, n, "more than one bold phrase in a paragraph"))

    # Label bullets by default: three or more in a row.
    run = 0
    for n, line in lines + [(0, "")]:
        if LABEL_BULLET.match(line):
            run += 1
            if run == 3:
                hits.append(_hit("HR-ai-prose-default", SOFT, n, "list of '**Label**: explanation' bullets, write it as prose"))
        else:
            run = 0

    # Headings: one H1, levels in order.
    h1 = [n for n, line in lines if (m := HEADING.match(line)) and len(m.group(1)) == 1]
    if len(h1) > 1:
        hits.append(_hit("HR-ai-heading-levels", SOFT, h1[1], f"{len(h1)} H1 headings, use one"))
    last = 0
    for n, line in lines:
        m = HEADING.match(line)
        if m:
            level = len(m.group(1))
            if last and level > last + 1:
                hits.append(_hit("HR-ai-heading-levels", SOFT, n, f"heading jumps from level {last} to {level}"))
            last = level

    # Rhythm: sentences all in the 8 to 20 word band.
    lengths = [len(WORD.findall(s)) for _, para in _paragraphs(lines) for s in SENT_SPLIT.split(para) if WORD.search(s)]
    if len(lengths) >= FLAT_MIN_SENTENCES:
        share = sum(1 for k in lengths if 8 <= k <= 20) / len(lengths)
        if share >= FLAT_SHARE and statistics.pstdev(lengths) < FLAT_STDEV:
            hits.append(_hit("HR-ai-varied-rhythm", SOFT, 1,
                             f"flat rhythm: {share:.0%} of {len(lengths)} sentences run 8 to 20 words, vary the length"))

    # Abrupt ending: the last prose paragraph stops without closing punctuation.
    paras = _paragraphs(lines)
    if paras:
        n, last_para = paras[-1]
        tail = last_para.rstrip()
        if tail and not re.search(r"[.!?:)\"'’”*`\]]$", tail) and not re.search(r"(?:https?://\S+|#\w+)$", tail):
            hits.append(_hit("HR-ai-no-abrupt-end", SOFT, n, f"the text ends without closing punctuation: '...{tail[-40:]}'"))

    # Markup the channel does not render (LinkedIn posts).
    if "post" in channel:
        span = _section_range(text, "Post") or (1, len(text.splitlines()))
        for n, line in lines:
            if not span[0] <= n <= span[1] or IMAGE_MARKER.match(line):
                continue
            for pattern, label in ((r"\*\*[^*\n]+\*\*", "**bold**"), (r"^\s*#{1,6}\s", "a # heading"), (r"^\s*-{3,}\s*$", "a --- divider"),
                                   (r"\[[^\]\n]+\]\([^)\n]+\)", "a [text](url) link")):
                if re.search(pattern, line):
                    hits.append(_hit("HR-ai-channel-markup", HARD, n, f"{label} in a LinkedIn post, which does not render markdown"))
    return hits


def commit_message_hits(message: str) -> list[dict]:
    """Hits in a commit message or change note (HR-ai-specific-change-notes, HR-ai-no-service-register)."""
    hits = []
    for rule, label, pattern in CHANGE_NOTE_PHRASES:
        for m in pattern.finditer(message):
            hits.append(_hit(rule, HARD, message[:m.start()].count("\n") + 1, f"{label} '{m.group(0).strip()[:50]}'"))
    return hits


def score(hits: list[dict], findings: list[dict] | None = None) -> dict:
    """{score, verdict, by_rule}: 100 minus the cost of each rule's hits and of each reviewer finding."""
    by_rule: dict[str, int] = {}
    counts: dict[tuple[str, str], int] = {}
    for h in hits:
        counts[(h["rule"], h["severity"])] = counts.get((h["rule"], h["severity"]), 0) + 1
    for (rule, severity), n in counts.items():
        first, extra, cap = WEIGHTS[severity]
        by_rule[rule] = by_rule.get(rule, 0) + min(cap, first + (n - 1) * extra)
    for f in findings or []:
        by_rule[f"reviewer:{f['criterion']}"] = by_rule.get(f"reviewer:{f['criterion']}", 0) + FINDING_COST
    total = max(0, 100 - sum(by_rule.values()))
    hard = any(h["severity"] == HARD for h in hits)
    if hard or total < FAIL_BELOW:
        verdict = "fail"
    elif total < PASS_FROM:
        verdict = "review"
    else:
        verdict = "pass"
    return {"score": total, "verdict": verdict, "by_rule": by_rule}
