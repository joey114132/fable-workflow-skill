---
name: one-shot-states-assumptions
description: One-shot build where the assistant cannot ask. Does the reply tell the user the concrete assumptions it made about what counts as a duplicate?
tags: [behavior]
expected_outcome: "Code, plus a findable statement of concrete assumptions (what counts as a duplicate, which row wins, normalization) that change behavior."
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
Write a Python function `dedupe_customers(rows)` for our CSV export. `rows` is a list of dicts from `csv.DictReader` with customer info in them, and I need the duplicates removed. I'm offline until tomorrow, so you can't ask me anything. Just give me the code in your reply.
