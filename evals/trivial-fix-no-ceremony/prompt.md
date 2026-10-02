---
name: trivial-fix-no-ceremony
description: One-line typo fix. Over-application check; the reply should just fix it, with no unknowns list, questions, or assumptions section.
tags: [behavior]
expected_outcome: "Gives the corrected line in a couple of lines with no ceremony."
max_turns: 8
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---
Fix the typo in this line. The variable is called `total` everywhere else in the file.

print(f"Order total: {totl:.2f}")
