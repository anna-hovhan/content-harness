---
description: Plan the visuals for a draft, write the placement map and the commands (design-assistant, or the Portfolio repo for site images), and put the image markers in the draft
argument-hint: "<piece folder or draft path>"
disable-model-invocation: true
---

Plan the visuals for: $ARGUMENTS

1. Find the piece folder in `workspace/pieces/` (or the draft path given).
2. Run `system/00-core/visual-handoff.md`, steps 1 to 3. Ask before making the visuals (steps 4 and 5).
3. Check with `python3 scripts/test_check_text.py <draft.md> --visuals <visuals.md>`.
