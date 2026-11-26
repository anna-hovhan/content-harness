"""Post types for LinkedIn posts (system/20-linkedin-posts/post-types/): every type file has the sections the
folder's README lists, a goal, a "Use it when" line the workflow can match, a word cap its check command uses, a
template that keeps the sections the checkers read, a "Where it differs" table when the user set rules for it, and
text that passes the house-rule check.

The workflow finds the types by listing the folder at run time, so a new type is one new file; these tests read
every file there. Fixtures are invented and generic. Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import test_check_text  # noqa: E402

POSTS = ROOT / "system" / "20-linkedin-posts"
TYPES = POSTS / "post-types"
README = TYPES / "README.md"
WORKFLOW = POSTS / "linkedin-post.md"
SKILL = ROOT / ".claude" / "skills" / "write-linkedin-post" / "SKILL.md"
STANDARD_TEMPLATE = POSTS / "templates" / "post.md"

# The sections every type file has, in this order (post-types/README.md, "What every type file has").
SECTIONS = ["Source", "Before drafting", "Gather", "Shape", "What stays out", "Image", "Check", "After it is live"]
HEADER_LINES = ["Goal", "Use it when", "Not for", "Word cap", "Template"]
TEMPLATE_PARTS = [r"^\*\*Status:\*\*", r"^## Post\s*$", r"^## Other hooks to try\s*$", r"^## Check before posting\s*$"]
PROVENANCE = re.compile(r"^\*(?:From the source|From the user|This repo)\b")
WORKFLOW_CAP = 200


def type_files() -> list[Path]:
    return sorted(p for p in TYPES.glob("*.md") if p.name != "README.md")


def header_value(text: str, label: str) -> str | None:
    head = text.split("\n## ", 1)[0]
    m = re.search(rf"^\*\*{re.escape(label)}:\*\*\s*(.+)$", head, re.M)
    return m.group(1).strip() if m else None


def section(text: str, name: str) -> str:
    """The body of the '## <name>' section (a heading may go on after a colon), up to the next '## '."""
    m = re.search(rf"^## {re.escape(name)}(?::[^\n]*)?\s*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def word_cap(text: str) -> int | None:
    value = header_value(text, "Word cap") or ""
    m = re.search(r"(\d+)\s+words", value)
    return int(m.group(1)) if m else None


def problems(text: str) -> list[str]:
    """What a type file is missing or has out of order; an empty list when it is complete."""
    found = []
    if not re.match(r"# Post type: \S", text):
        found.append("the title is not '# Post type: <name>'")
    for label in HEADER_LINES:
        if not header_value(text, label):
            found.append(f"no '**{label}:**' line under the title")
    headings = re.findall(r"^## (.+?)\s*$", text, re.M)
    last = -1
    for name in SECTIONS:
        hits = [i for i, h in enumerate(headings) if h == name or h.startswith(name + ":")]
        if not hits:
            found.append(f"no '## {name}' section")
        elif hits[0] < last:
            found.append(f"'## {name}' is out of order")
        else:
            last = hits[0]
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^#{2,3} ", line):
            following = next((l for l in lines[i + 1:] if l.strip()), "")
            if not PROVENANCE.match(following):
                found.append(f"'{line.strip()}' does not open with where it comes from (*From the source*, *From the user* or *This repo*)")
    cap = word_cap(text)
    if cap is None:
        found.append("the '**Word cap:**' line gives no number of words")
    elif f"--max-words {cap}" not in section(text, "Check"):
        found.append(f"the Check section does not run the checker with --max-words {cap}")
    return found


def template_path(text: str) -> Path | None:
    m = re.search(r"`([^`]+\.md)`", header_value(text, "Template") or "")
    return ROOT / m.group(1) if m else None


# An invented type, complete except for its Check section.
INCOMPLETE_TYPE = """# Post type: a talk recap

**Goal:** peers see the talk's one claim and what the room asked.
**Use it when:** the post recaps a talk the user gave.
**Not for:** a talk the user only attended.
**Word cap:** at most 150 words, hook to close.
**Template:** `system/20-linkedin-posts/templates/post.md`, copied as `draft.md`.

## Source

*This repo.* Written here, with no outside source.

## Before drafting

*This repo.* Is the recording public?

## Gather

*This repo.* The slides and the user's notes.

## Shape

*This repo.* The talk's one claim, then the question from the room.

## What stays out

*This repo.* The full abstract.

## Image

*This repo.* A photo from the talk, with the speaker's yes.

## After it is live

*This repo.* Step 6 as usual.
"""

# Line 2 ("What you learned") of a leaving post: written as the type says, and in the banned frame.
FINDING_LINES = [
    "Most of the fixes that moved that number came from reading support tickets with the support lead every Monday.",
    "Writing the data contracts with the analysts before writing any pipeline code saved more rework than any tool we added later.",
]
# Line 2 with the short label of the user's own example: the lesson follows in the same sentence, and it passes.
LABELLED_LESSON_LINES = [
    "Biggest lesson: transformation moved at the speed of leadership alignment.",
    "Biggest lesson: the checkout fixes paid off only after finance and marketing agreed on one definition of a returning customer.",
]
LESSON_FRAME_LINES = [
    "Here's what those years at [employer] taught me about product work.",
    "What I learned: ship small and talk to support every week.",
    "The biggest lesson I learned there is to ship small.",
]
# An invented leaving post in the type's four lines.
FOUR_LINES = [
    "I left [employer] last month, after building the data pipeline behind its pricing models, which cut the analysts' weekly refresh time by 90%.",
    FINDING_LINES[1],
    "I'm looking for a staff data engineering role on a product team that trains and ships its own models, in [place] or remote.",
    "If your team is hiring for that, or you want to talk about data contracts, my messages here are open.",
]


# An invented leaving post in the user's own example lines: two sentences in line 1, a metric as a before and after
# pair, the time in the role, and the labelled lesson.
USER_SHAPE_LINES = [
    "I spent the last 6 years growing the digital business for a global consumer products company. We grew the revenue from 12 million to 40 million.",
    LABELLED_LESSON_LINES[0],
    "Next up I am joining [new employer] to lead digital and growth.",
    "If you work on digital growth, message me here.",
]


def users_examples(text: str) -> list[str]:
    """The quoted sentences in the last column of the table that opens '## Shape' (the user's own examples)."""
    table = section(text, "Shape").split("\n### ", 1)[0]
    rows = [r.strip().strip("|").split("|") for r in table.splitlines() if r.startswith("| ")]
    cells = [r[-1].strip() for r in rows[1:]]
    return [q for c in cells if not c.startswith("None") for q in re.findall(r'"([^"]+)"', c)]


def fill_post(template: str, lines: list[str]) -> str:
    """The template with its '## Post' placeholders replaced by the given lines."""
    head, rest = template.split("## Post", 1)
    body, tail = re.split(r"(?=^## )", rest, maxsplit=1, flags=re.M)
    post = "\n\n" + "\n\n".join(lines) + "\n\n[IMAGE v1: slug]\n\n"
    return head + "## Post" + post + tail


class TypeFolderTests(unittest.TestCase):
    def test_the_folder_holds_at_least_one_type(self):
        self.assertTrue(README.exists())

    def test_the_readme_lists_the_sections_these_tests_require(self):
        listed = re.findall(r"^\d+\. `## ([^`]+)`", README.read_text(encoding="utf-8"), re.M)
        self.assertEqual(listed, SECTIONS)
        for label in HEADER_LINES:
            self.assertIn(f"`**{label}:**`", README.read_text(encoding="utf-8"))

    def test_the_section_check_catches_a_missing_section(self):
        self.assertIn("no '## Check' section", problems(INCOMPLETE_TYPE))

    def test_every_type_file_has_its_lines_and_sections_in_order(self):
        for path in type_files():
            with self.subTest(type=path.name):
                self.assertEqual(problems(path.read_text(encoding="utf-8")), [])

    def test_no_two_types_share_a_use_it_when_line(self):
        lines = [header_value(p.read_text(encoding="utf-8"), "Use it when") for p in type_files()]
        self.assertEqual(len(lines), len(set(lines)))

    def test_a_type_with_rules_from_the_user_lists_where_it_differs(self):
        self.assertIn("`## Where it differs`", README.read_text(encoding="utf-8"))
        for path in type_files():
            text = path.read_text(encoding="utf-8")
            if not re.search(r"^\*From the user\b", text, re.M):
                continue
            with self.subTest(type=path.name):
                # The header row and at least one rule; the separator row starts with "|-" and is not counted.
                rows = [r for r in section(text, "Where it differs").splitlines() if r.startswith("| ")]
                self.assertGreaterEqual(len(rows), 2, "no table under '## Where it differs'")
                self.assertIn("The rule above", rows[0])

    def test_every_word_cap_is_within_the_workflow_cap(self):
        for path in type_files():
            with self.subTest(type=path.name):
                cap = word_cap(path.read_text(encoding="utf-8"))
                self.assertIsNotNone(cap)
                self.assertLessEqual(cap, WORKFLOW_CAP)


class WorkflowTests(unittest.TestCase):
    def test_the_workflow_lists_the_folder(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("system/20-linkedin-posts/post-types/", text)
        self.assertIn("Use it when", text)

    def test_the_skill_mentions_post_types(self):
        self.assertIn("post type", SKILL.read_text(encoding="utf-8"))

    def test_the_workflow_and_the_skill_name_no_single_type(self):
        # A new type must need no edit to either file: they find the types by listing the folder.
        for path in type_files():
            name = path.read_text(encoding="utf-8").splitlines()[0].removeprefix("# Post type: ").strip()
            for other in (WORKFLOW, SKILL):
                with self.subTest(type=path.name, file=other.name):
                    text = other.read_text(encoding="utf-8")
                    self.assertNotIn(path.stem, text)
                    self.assertNotIn(name, text)


class TemplateTests(unittest.TestCase):
    def test_every_type_names_a_template_that_exists(self):
        for path in type_files():
            with self.subTest(type=path.name):
                template = template_path(path.read_text(encoding="utf-8"))
                self.assertIsNotNone(template)
                self.assertTrue(template.exists(), template)

    def test_a_type_template_keeps_the_sections_the_checkers_read(self):
        for path in type_files():
            template = template_path(path.read_text(encoding="utf-8"))
            if template is None or template == STANDARD_TEMPLATE:
                continue
            text = template.read_text(encoding="utf-8")
            for part in TEMPLATE_PARTS:
                with self.subTest(template=template.name, part=part):
                    self.assertRegex(text, re.compile(part, re.M))


class TextTests(unittest.TestCase):
    def test_the_type_files_and_templates_pass_the_text_check(self):
        files = [README] + type_files()
        files += [t for t in (template_path(p.read_text(encoding="utf-8")) for p in type_files()) if t and t.exists()]
        for path in files:
            with self.subTest(file=path.name):
                self.assertEqual(test_check_text.check(path.read_text(encoding="utf-8"))["errors"], [])

    def test_the_example_lines_in_each_type_pass_the_text_check(self):
        for path in type_files():
            examples = re.findall(r'Example: "([^"]+)"', path.read_text(encoding="utf-8"))
            self.assertTrue(examples, path.name)
            for line in examples:
                with self.subTest(type=path.name, line=line):
                    self.assertEqual(test_check_text.check(line, channel="LinkedIn post")["errors"], [])

    def test_a_finding_passes_and_the_lesson_frame_fails(self):
        for line in FINDING_LINES + LABELLED_LESSON_LINES:
            self.assertEqual(test_check_text.check(line, channel="LinkedIn post")["errors"], [], line)
        for line in LESSON_FRAME_LINES:
            self.assertTrue(test_check_text.check(line, channel="LinkedIn post")["errors"], line)


if __name__ == "__main__":
    unittest.main()
